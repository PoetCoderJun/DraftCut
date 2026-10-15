#!/usr/bin/env python3
"""Build a conservative, agent-reviewable edit plan from word timestamps."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Optional


FILLERS = {
    "嗯",
    "呃",
    "额",
    "呣",
    "唔",
    "em",
    "erm",
    "uh",
    "um",
}


def number(value: float) -> float:
    return round(float(value), 6)


def normalize_word(text: str) -> str:
    return re.sub(r"[\W_]+", "", text, flags=re.UNICODE).lower()


def flatten_words(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    words = [
        word
        for segment in transcript.get("segments", [])
        for word in segment.get("words", [])
        if str(word.get("text", "")).strip()
    ]
    words.sort(key=lambda item: (float(item["start"]), float(item["end"])))
    return words


def base_keep_segments(
    words: list[dict[str, Any]],
    *,
    source_duration: float,
    max_pause: float,
    keep_pause: float,
    edge_padding: float,
) -> list[dict[str, float]]:
    if not words:
        raise ValueError("transcript contains no word timestamps")
    if max_pause <= 0 or keep_pause < 0 or keep_pause > max_pause:
        raise ValueError("require 0 <= keep_pause <= max_pause")
    if edge_padding < 0:
        raise ValueError("edge_padding must be non-negative")

    half_pause = keep_pause / 2
    raw_segments: list[tuple[float, float]] = []
    start = max(0.0, float(words[0]["start"]) - edge_padding)
    previous_end = float(words[0]["end"])

    for word in words[1:]:
        word_start = float(word["start"])
        word_end = float(word["end"])
        if word_start - previous_end > max_pause:
            raw_segments.append((start, min(source_duration, previous_end + half_pause)))
            start = max(0.0, word_start - half_pause)
        previous_end = max(previous_end, word_end)
    raw_segments.append((start, min(source_duration, previous_end + edge_padding)))

    output: list[dict[str, float]] = []
    out_start = 0.0
    for source_start, source_end in raw_segments:
        if source_end <= source_start:
            continue
        output.append(
            {
                "start": number(source_start),
                "end": number(source_end),
                "out_start": number(out_start),
            }
        )
        out_start += source_end - source_start
    return output


def review_items(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    previous: Optional[dict[str, Any]] = None
    for word in words:
        normalized = normalize_word(str(word["text"]))
        if normalized in FILLERS:
            items.append(
                {
                    "kind": "filler",
                    "word_ids": [word["id"]],
                    "source_start": number(word["start"]),
                    "source_end": number(word["end"]),
                    "instruction": "Listen before deleting; keep it if it carries meaning.",
                }
            )
        if (
            previous is not None
            and normalized
            and normalized == normalize_word(str(previous["text"]))
            and float(word["start"]) - float(previous["end"]) <= 0.8
        ):
            items.append(
                {
                    "kind": "immediate_repeat",
                    "candidate_delete": [previous["id"]],
                    "preferred_keep": word["id"],
                    "source_start": number(previous["start"]),
                    "source_end": number(previous["end"]),
                    "instruction": "Prefer the later take after listening for continuity.",
                }
            )
        previous = word
    return items


def build_draft_plan(
    transcript: dict[str, Any],
    *,
    max_pause: float = 0.65,
    keep_pause: float = 0.22,
    edge_padding: float = 0.12,
) -> dict[str, Any]:
    if transcript.get("version") != "talking-head-transcript.v1":
        raise ValueError("unsupported transcript version")
    source_duration = float(transcript.get("duration_seconds", 0.0))
    if not math.isfinite(source_duration) or source_duration <= 0:
        raise ValueError("transcript duration_seconds must be positive")
    words = flatten_words(transcript)
    return {
        "version": "talking-head-edit-plan.v1",
        "source": transcript.get("source"),
        "source_duration_seconds": number(source_duration),
        "base_keep_segments": base_keep_segments(
            words,
            source_duration=source_duration,
            max_pause=max_pause,
            keep_pause=keep_pause,
            edge_padding=edge_padding,
        ),
        "delete_ranges": [],
        "review_items": review_items(words),
        "subtitles": [
            {
                "id": segment["id"],
                "source_start": number(segment["start"]),
                "source_end": number(segment["end"]),
                "text": str(segment.get("text", "")).strip(),
            }
            for segment in transcript.get("segments", [])
            if str(segment.get("text", "")).strip()
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a pause-compressed draft plan for agent review."
    )
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-pause", type=float, default=0.65)
    parser.add_argument("--keep-pause", type=float, default=0.22)
    parser.add_argument("--edge-padding", type=float, default=0.12)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    transcript = json.loads(args.transcript.read_text(encoding="utf-8"))
    plan = build_draft_plan(
        transcript,
        max_pause=args.max_pause,
        keep_pause=args.keep_pause,
        edge_padding=args.edge_padding,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"edit_plan": str(args.output.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
