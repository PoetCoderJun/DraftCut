#!/usr/bin/env python3
"""Transcribe one spoken video to word-timestamped JSON and a draft SRT."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import urlsplit


DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com"
DEFAULT_DASHSCOPE_MODEL = "qwen3-asr-flash-filetrans"


class DashScopeError(RuntimeError):
    """A service failure containing only locally authored, safe diagnostic text."""


class DashScopeSettings:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        language: Optional[str],
        poll_seconds: float,
        timeout_seconds: float,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.language = language
        self.poll_seconds = poll_seconds
        self.timeout_seconds = timeout_seconds


def report_progress(step: int, total: int, message: str) -> None:
    """Write a compact progress update without polluting stdout JSON."""
    print(f"[{step}/{total}] {message}", file=sys.stderr, flush=True)


def dashscope_api_key(environ: Mapping[str, str]) -> str:
    return next((str(environ.get(name) or '').strip()
                 for name in ('DASHSCOPE_ASR_API_KEY', 'DASHSCOPE_API_KEY')
                 if str(environ.get(name) or '').strip()), '')


def normalize_dashscope_base_url(value: str) -> str:
    base_url = str(value or DEFAULT_DASHSCOPE_BASE_URL).strip().rstrip("/")
    try:
        parsed = urlsplit(base_url)
    except ValueError:
        raise ValueError('DASHSCOPE_ASR_BASE_URL / DASHSCOPE_BASE_URL is not a valid HTTPS service URL') from None
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment):
        raise ValueError('DASHSCOPE_ASR_BASE_URL / DASHSCOPE_BASE_URL must be an HTTPS URL without credentials, query or fragment')
    for suffix in ("/compatible-mode/v1", "/api/v1"):
        if base_url.endswith(suffix):
            return base_url[: -len(suffix)]
    return base_url


def dashscope_settings(
    environ: Mapping[str, str],
    *,
    language: Optional[str],
) -> DashScopeSettings:
    api_key = dashscope_api_key(environ)
    if not api_key:
        raise RuntimeError('DashScope transcription needs DASHSCOPE_API_KEY (or DASHSCOPE_ASR_API_KEY). '
                           'Configure once with configure_asr.py setup, inject it securely, or select --env-file with transcribe_audio.py. '
                           'A trusted word-timestamp transcript can be imported without a cloud key.')
    def interval(name, default, minimum):
        try:
            value = float(environ.get(name) or default)
        except (ValueError, TypeError):
            raise ValueError(f'{name} must be a finite positive number') from None
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f'{name} must be a finite positive number')
        return max(minimum, value)
    return DashScopeSettings(
        base_url=normalize_dashscope_base_url(
            str(
                environ.get("DASHSCOPE_ASR_BASE_URL")
                or environ.get("DASHSCOPE_BASE_URL")
                or DEFAULT_DASHSCOPE_BASE_URL
            )
        ),
        api_key=api_key,
        model=str(
            environ.get("DASHSCOPE_ASR_MODEL") or DEFAULT_DASHSCOPE_MODEL
        ).strip(),
        language=(str(language).strip() if language else None),
        poll_seconds=interval('DASHSCOPE_ASR_POLL_SECONDS', 2.0, 0.5),
        timeout_seconds=interval('DASHSCOPE_ASR_TIMEOUT_SECONDS', 3600.0, 30.0),
    )


def _requests_session() -> Any:
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError(
            "requests is not installed; run: "
            "python -m pip install -r requirements.txt"
        ) from exc
    return requests.Session()


def _check_response(response: Any, *, stage: str) -> None:
    try:
        response.raise_for_status()
    except Exception as exc:
        # Service bodies may echo credentials, prompt text or signed upload URLs.
        status = getattr(response, 'status_code', None)
        label = f' (HTTP {status})' if isinstance(status, int) else ''
        raise DashScopeError(f'DashScope {stage} failed{label}; check account region, model access, quota and network. Service response withheld.') from exc


def upload_to_dashscope_temporary(
    audio_path: Path,
    *,
    settings: DashScopeSettings,
    session: Optional[Any] = None,
) -> str:
    """Stream audio through DashScope-issued temporary credentials."""
    try:
        from requests_toolbelt import MultipartEncoder
    except ImportError as exc:
        raise RuntimeError(
            "requests-toolbelt is not installed; run: "
            "python -m pip install -r requirements.txt"
        ) from exc

    client = session or _requests_session()
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    policy_response = client.get(
        settings.base_url + "/api/v1/uploads",
        params={"action": "getPolicy", "model": settings.model},
        headers=headers,
        timeout=settings.timeout_seconds,
    )
    _check_response(policy_response, stage="temporary upload policy")
    try:
        policy = policy_response.json()["data"]
        upload_dir = str(policy["upload_dir"]).strip().strip("/")
        upload_host = str(policy["upload_host"]).strip()
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "DashScope temporary upload policy response is incomplete"
        ) from exc

    max_size_mb = float(policy.get("max_file_size_mb") or 0.0)
    if max_size_mb > 0 and audio_path.stat().st_size > max_size_mb * 1024 * 1024:
        raise RuntimeError(
            f"DashScope temporary upload limit is {max_size_mb:g} MB"
        )

    safe_name = "".join(
        char if char.isalnum() or char in {".", "-", "_"} else "_"
        for char in audio_path.name
    )
    object_key = f"{upload_dir}/{uuid.uuid4().hex[:12]}-{safe_name}"
    with audio_path.open("rb") as audio_file:
        encoder = MultipartEncoder(
            fields=[
                ("OSSAccessKeyId", str(policy["oss_access_key_id"])),
                ("Signature", str(policy["signature"])),
                ("policy", str(policy["policy"])),
                ("x-oss-object-acl", str(policy["x_oss_object_acl"])),
                (
                    "x-oss-forbid-overwrite",
                    str(policy["x_oss_forbid_overwrite"]),
                ),
                ("key", object_key),
                ("success_action_status", "200"),
                ("file", (audio_path.name, audio_file, "audio/ogg")),
            ]
        )
        upload_response = client.post(
            upload_host,
            data=encoder,
            headers={
                "Content-Type": encoder.content_type,
                "Content-Length": str(encoder.len),
            },
            timeout=settings.timeout_seconds,
        )
    _check_response(upload_response, stage="temporary file upload")
    return "oss://" + object_key


def _dashscope_headers(
    settings: DashScopeSettings,
    *,
    resolve_temporary_file: bool,
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    if resolve_temporary_file:
        headers["X-DashScope-Async"] = "enable"
        headers["X-DashScope-OssResourceResolve"] = "enable"
    return headers


def _transcription_url(output: dict[str, Any]) -> str:
    direct = str(output.get("transcription_url") or "").strip()
    if direct:
        return direct
    nested = output.get("result")
    if isinstance(nested, dict):
        value = str(nested.get("transcription_url") or "").strip()
        if value:
            return value
    results = output.get("results")
    if isinstance(results, list):
        for item in results:
            if isinstance(item, dict):
                value = str(item.get("transcription_url") or "").strip()
                if value:
                    return value
    return ""


def transcribe_dashscope_task(
    audio_path: Path,
    *,
    settings: DashScopeSettings,
    prompt: str,
    session: Optional[Any] = None,
) -> dict[str, Any]:
    client = session or _requests_session()
    file_url = upload_to_dashscope_temporary(
        audio_path,
        settings=settings,
        session=client,
    )
    parameters: dict[str, Any] = {
        "channel_id": [0],
        "enable_itn": False,
        "enable_words": True,
    }
    if settings.language:
        parameters["language"] = settings.language
    if str(prompt or "").strip():
        parameters["corpus"] = {"text": str(prompt).strip()}
    submit_response = client.post(
        settings.base_url + "/api/v1/services/audio/asr/transcription",
        headers=_dashscope_headers(
            settings,
            resolve_temporary_file=True,
        ),
        json={
            "model": settings.model,
            "input": {"file_url": file_url},
            "parameters": parameters,
        },
        timeout=settings.timeout_seconds,
    )
    _check_response(submit_response, stage="task submission")
    try:
        task_id = str(submit_response.json()["output"]["task_id"]).strip()
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("DashScope task response is missing task_id") from exc
    if not task_id:
        raise RuntimeError("DashScope task response is missing task_id")

    deadline = time.monotonic() + settings.timeout_seconds
    transcription_url = ""
    last_status = ""
    while time.monotonic() < deadline:
        poll_response = client.get(
            settings.base_url + f"/api/v1/tasks/{task_id}",
            headers=_dashscope_headers(
                settings,
                resolve_temporary_file=False,
            ),
            timeout=settings.timeout_seconds,
        )
        _check_response(poll_response, stage="task polling")
        output = poll_response.json().get("output")
        if not isinstance(output, dict):
            output = {}
        last_status = str(output.get("task_status") or "RUNNING").upper()
        transcription_url = _transcription_url(output)
        if last_status == "SUCCEEDED" and transcription_url:
            break
        if last_status in {"FAILED", "CANCELED", "CANCELLED"}:
            raise DashScopeError(f'DashScope task {last_status}; check account region, model access and quota. Service message withheld.')
        time.sleep(settings.poll_seconds)
    if not transcription_url:
        raise DashScopeError(
            'DashScope task timed out; check network access and service status'
        )

    result_response = client.get(
        transcription_url,
        timeout=settings.timeout_seconds,
    )
    _check_response(result_response, stage="result download")
    payload = result_response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("DashScope transcription result is not a JSON object")
    return payload


def probe_duration(source: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(source),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    duration = float(json.loads(result.stdout)["format"]["duration"])
    if duration <= 0:
        raise RuntimeError("source duration must be positive")
    return seconds(duration)


def extract_audio_proxy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-vn",
            "-ac",
            "1",
            "-ar",
            "48000",
            "-c:a",
            "libopus",
            "-b:a",
            "32k",
            str(destination),
        ],
        check=True,
    )


def is_extracted_audio_duration_complete(
    source_duration: float,
    audio_duration: float,
) -> bool:
    if source_duration <= 0 or audio_duration <= 0:
        return False
    allowed_gap = max(3.0, source_duration * 0.03)
    return audio_duration + allowed_gap >= source_duration


def dashscope_result_to_transcript(
    result: dict[str, Any],
    *,
    source: Path,
    source_duration: float,
) -> dict[str, Any]:
    serialized_segments: list[dict[str, Any]] = []
    global_word_index = 0
    language: Optional[str] = None
    max_end = 0.0

    transcripts = result.get("transcripts")
    if not isinstance(transcripts, list):
        transcripts = []
    for transcript in transcripts:
        if not isinstance(transcript, dict):
            continue
        language = language or str(transcript.get("language") or "").strip() or None
        sentences = transcript.get("sentences")
        if not isinstance(sentences, list):
            continue
        for sentence in sentences:
            if not isinstance(sentence, dict):
                continue
            raw_words = sentence.get("words")
            if not isinstance(raw_words, list):
                raw_words = []
            words: list[dict[str, Any]] = []
            for raw_word in raw_words:
                if not isinstance(raw_word, dict):
                    continue
                try:
                    start = seconds(float(raw_word["begin_time"]) / 1000.0)
                    end = seconds(float(raw_word["end_time"]) / 1000.0)
                except (KeyError, TypeError, ValueError):
                    continue
                text = (
                    str(raw_word.get("text") or "")
                    + str(raw_word.get("punctuation") or "")
                ).strip()
                if not text or end <= start:
                    continue
                global_word_index += 1
                words.append(
                    {
                        "id": f"word-{global_word_index:06d}",
                        "start": start,
                        "end": end,
                        "text": text,
                    }
                )
            if not words:
                continue
            try:
                sentence_start = seconds(
                    float(sentence.get("begin_time")) / 1000.0
                )
                sentence_end = seconds(
                    float(sentence.get("end_time")) / 1000.0
                )
            except (TypeError, ValueError):
                sentence_start = words[0]["start"]
                sentence_end = words[-1]["end"]
            if sentence_end <= sentence_start:
                sentence_start = words[0]["start"]
                sentence_end = words[-1]["end"]
            text = str(sentence.get("text") or "").strip()
            if not text:
                text = "".join(str(word["text"]) for word in words)
            serialized_segments.append(
                {
                    "id": f"seg-{len(serialized_segments) + 1:04d}",
                    "start": sentence_start,
                    "end": sentence_end,
                    "text": text,
                    "words": words,
                }
            )
            language = language or str(sentence.get("language") or "").strip() or None
            max_end = max(max_end, sentence_end)

    if not serialized_segments or global_word_index == 0:
        raise RuntimeError(
            "DashScope returned no word timestamps; "
            "qwen3-asr-flash-filetrans with enable_words=true is required"
        )
    serialized_segments.sort(key=lambda item: (item["start"], item["end"]))
    return {
        "version": "talking-head-transcript.v1",
        "provider": "dashscope",
        "source": str(source.resolve()),
        "duration_seconds": seconds(max(source_duration, max_end)),
        "language": language,
        "language_probability": 0.0,
        "segments": serialized_segments,
    }


def transcribe_dashscope(
    source: Path,
    *,
    output_dir: Path,
    settings: DashScopeSettings,
    prompt: str,
) -> dict[str, Any]:
    audio_path = output_dir / "dashscope-input.ogg"
    report_progress(1, 4, "正在生成完整时长的单声道 Opus 音频代理")
    source_duration = probe_duration(source)
    extract_audio_proxy(source, audio_path)
    audio_duration = probe_duration(audio_path)
    if not is_extracted_audio_duration_complete(source_duration, audio_duration):
        raise RuntimeError(
            "音频提取不完整："
            f"源文件约 {source_duration:.2f} 秒，音频代理约 {audio_duration:.2f} 秒；"
            "已停止上传"
        )
    report_progress(2, 4, "正在流式上传音频到 DashScope 48 小时临时存储")
    report_progress(
        3,
        4,
        f"正在使用 {settings.model} 生成逐词时间戳",
    )
    try:
        result = transcribe_dashscope_task(
            audio_path,
            settings=settings,
            prompt=prompt,
        )
    except DashScopeError:
        raise
    except Exception as exc:
        raise RuntimeError('DashScope transcription failed; check network access, account region, model permission and quota. '
                           'Service details and temporary URLs are withheld.') from exc
    payload = dashscope_result_to_transcript(
        result,
        source=source,
        source_duration=source_duration,
    )
    report_progress(
        4,
        4,
        f"DashScope 转写完成：{len(payload['segments'])} 个片段",
    )
    return payload


def seconds(value: Any) -> float:
    return round(max(0.0, float(value)), 6)


def format_srt_timestamp(value: float) -> str:
    total_ms = max(0, round(float(value) * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcript_to_srt(transcript: dict[str, Any]) -> str:
    blocks: list[str] = []
    for index, segment in enumerate(transcript.get("segments", []), start=1):
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        blocks.append(
            f"{index}\n"
            f"{format_srt_timestamp(float(segment['start']))} --> "
            f"{format_srt_timestamp(float(segment['end']))}\n"
            f"{text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a word-timestamped transcript for one spoken video."
    )
    parser.add_argument("--input", type=Path, required=True, help="Source video or audio")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--language", help="Optional ISO language code, for example zh or en")
    parser.add_argument(
        "--prompt",
        default="",
        help="Optional terms or context to improve ASR recognition",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    settings = dashscope_settings(os.environ, language=args.language)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    payload = transcribe_dashscope(
        args.input,
        output_dir=args.output_dir,
        settings=settings,
        prompt=args.prompt,
    )
    transcript_path = args.output_dir / "transcript.json"
    draft_srt_path = args.output_dir / "draft.srt"
    transcript_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    draft_srt_path.write_text(transcript_to_srt(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "transcript": str(transcript_path.resolve()),
                "draft_srt": str(draft_srt_path.resolve()),
                "provider": "dashscope",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
