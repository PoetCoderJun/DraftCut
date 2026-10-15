#!/usr/bin/env python3
"""Prepare an audio-only master and aligned SRT after an explicit breath decision."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from vendor.clean_talking_video.transcribe import transcript_to_srt

SAMPLE_RATE = 48000

def run(*args: object) -> str:
    return subprocess.check_output([str(a) for a in args], text=True, stderr=subprocess.PIPE)

def probe(file: Path) -> dict:
    return json.loads(run('ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', file))

def audio_duration(file: Path) -> float:
    info = probe(file)
    audio = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
    if audio is None:
        raise ValueError('Input has no audio stream')
    duration = float(audio.get('duration') or info['format']['duration'])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Audio duration must be finite and positive')
    return duration

def validate_transcript(transcript: dict, duration: float) -> None:
    if not isinstance(transcript.get('segments'), list) or not transcript['segments']:
        raise ValueError('Transcript must contain timestamped segments')
    declared = float(transcript.get('duration_seconds', duration))
    if not math.isfinite(declared) or abs(declared - duration) > .1:
        raise ValueError('Transcript duration does not match the supplied audio')
    previous = -1.0
    for seg in transcript['segments']:
        start, end = float(seg['start']), float(seg['end'])
        if not all(math.isfinite(v) for v in (start, end)) or start < 0 or end <= start or end > duration + .00001 or start < previous:
            raise ValueError('Invalid or out-of-order transcript segment timestamps')
        previous = start
        if not str(seg.get('text', '')).strip():
            raise ValueError('Transcript segments need text')
        for word in seg.get('words', []):
            a, b = float(word['start']), float(word['end'])
            if not all(math.isfinite(v) for v in (a, b)) or a < 0 or b <= a or b > duration + .00001:
                raise ValueError('Invalid word timestamps')

def words(transcript: dict) -> list[dict]:
    return sorted([w for s in transcript['segments'] for w in s.get('words', [])], key=lambda w: float(w['start']))

def propose_gaps(transcript: dict, keep_gap: float = .25) -> dict:
    """Candidate word gaps are not breath detections and are never auto-approved."""
    result = []
    flattened = words(transcript)
    for left, right in zip(flattened, flattened[1:]):
        a, b = float(left['end']), float(right['start'])
        if b - a > keep_gap:
            result.append({'start': a, 'end': b, 'kind': 'unclassified', 'approved': False,
                           'reason': '', 'left_word': left.get('text'), 'right_word': right.get('text')})
    return {'status': 'needs_agent_listening_review', 'gaps': result,
            'note': 'Listen and classify. Preserve intentional pacing, emphasis and thinking pauses. Do not delete speech, fillers or retakes by default.'}

def selected_deletions(transcript: dict, review: dict, duration: float, keep_gap: float) -> list[tuple[int, int]]:
    if not math.isfinite(keep_gap) or keep_gap < 0:
        raise ValueError('keep_gap must be finite and non-negative')
    speech = words(transcript)
    if not speech:
        raise ValueError('Breath editing requires word timestamps for speech protection')
    selected = []
    for gap in review.get('gaps', []):
        if gap.get('approved') is not True:
            continue
        if gap.get('kind') != 'breath' or not str(gap.get('reason', '')).strip():
            raise ValueError('Selected gaps require kind=breath and a listening-review reason')
        a, b = float(gap['start']), float(gap['end'])
        if not all(math.isfinite(v) for v in (a, b)) or a < 0 or b <= a or b > duration:
            raise ValueError('Selected breath gap is outside the audio')
        if any(a < float(w['end']) - 1e-6 and b > float(w['start']) + 1e-6 for w in speech):
            raise ValueError('Breath gap overlaps speech; do not cut words or retakes')
        if b - a <= keep_gap:
            continue
        start, end = round(a * SAMPLE_RATE), round(b * SAMPLE_RATE)
        keep = round(keep_gap * SAMPLE_RATE)
        left = keep // 2
        selected.append((start + left, end - (keep - left)))
    selected.sort()
    if any(a[1] > b[0] for a, b in zip(selected, selected[1:])):
        raise ValueError('Selected breath gaps overlap')
    return selected

def keep_intervals(total_samples: int, deletions: list[tuple[int, int]]) -> list[tuple[int, int]]:
    intervals = []
    cursor = 0
    for start, end in deletions:
        if start < cursor or end <= start or end > total_samples:
            raise ValueError('Invalid deletion on sample timeline')
        if start > cursor:
            intervals.append((cursor, start))
        cursor = end
    if cursor < total_samples:
        intervals.append((cursor, total_samples))
    if not intervals:
        raise ValueError('Cannot delete the entire recording')
    return intervals

def map_time(value: float, deletions: list[tuple[int, int]]) -> float:
    sample = round(float(value) * SAMPLE_RATE)
    removed = sum(max(0, min(sample, end) - start) for start, end in deletions if sample > start)
    return round((sample - removed) / SAMPLE_RATE, 6)

def remap_transcript(transcript: dict, deletions: list[tuple[int, int]], duration: float) -> dict:
    result = copy.deepcopy(transcript)
    result['duration_seconds'] = duration
    for segment in result['segments']:
        segment['source_start'], segment['source_end'] = segment['start'], segment['end']
        segment['start'], segment['end'] = map_time(segment['start'], deletions), map_time(segment['end'], deletions)
        if segment['end'] <= segment['start']:
            raise ValueError('Editing removed a subtitle segment; review the selected gaps')
        for word in segment.get('words', []):
            word['source_start'], word['source_end'] = word['start'], word['end']
            word['start'], word['end'] = map_time(word['start'], deletions), map_time(word['end'], deletions)
    return result

def prepare(audio: Path, transcript: dict, output: Path, *, trim_breaths: str,
            review: dict | None = None, keep_gap: float = .25) -> dict:
    if trim_breaths not in ('yes', 'no'):
        raise ValueError('Ask the user whether to trim breath gaps; supply an explicit yes/no')
    if trim_breaths == 'no' and review is not None:
        raise ValueError('No-trim mode must not receive an edit review')
    if trim_breaths == 'yes' and review is None:
        raise ValueError('Breath editing needs reviewed gaps, not automatic silence removal')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty preparation directory; sources and prior output are preserved')
    if not audio.is_file():
        raise FileNotFoundError(audio)
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    if trim_breaths == 'yes' and review.get('audio_sha256') != digest:
        raise ValueError('Gap review must match the supplied audio SHA-256')
    duration = audio_duration(audio)
    validate_transcript(transcript, duration)
    output.mkdir(parents=True, exist_ok=True)
    normalized = output / 'normalized-source.wav'
    run('ffmpeg', '-v', 'error', '-xerror', '-n', '-i', audio, '-map', '0:a:0',
        '-af', 'aresample=48000,asetpts=PTS-STARTPTS', '-c:a', 'pcm_s24le', normalized)
    duration = audio_duration(normalized)
    total = round(duration * SAMPLE_RATE)
    cuts = selected_deletions(transcript, review or {}, duration, keep_gap) if trim_breaths == 'yes' else []
    intervals = keep_intervals(total, cuts)
    master = output / 'narration.wav'
    if not cuts:
        master.write_bytes(normalized.read_bytes())
    else:
        chains = [f'[0:a]atrim=start_sample={a}:end_sample={b},asetpts=PTS-STARTPTS[a{i}]' for i, (a, b) in enumerate(intervals)]
        chains.append(''.join(f'[a{i}]' for i in range(len(intervals))) + f'concat=n={len(intervals)}:v=0:a=1[out]')
        run('ffmpeg', '-v', 'error', '-xerror', '-n', '-i', normalized, '-filter_complex', ';'.join(chains),
            '-map', '[out]', '-ar', SAMPLE_RATE, '-c:a', 'pcm_s24le', master)
    expected = sum(b - a for a, b in intervals) / SAMPLE_RATE
    actual = audio_duration(master)
    if abs(actual - expected) > 1 / SAMPLE_RATE + 1e-6:
        raise ValueError('Prepared audio does not match the sample edit timeline')
    if review is not None:
        (output / 'gap-review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n')
    mapped = remap_transcript(transcript, cuts, expected)
    mapped['source'] = str(master.resolve())
    (output / 'transcript.json').write_text(json.dumps(mapped, ensure_ascii=False, indent=2) + '\n')
    (output / 'final.srt').write_text(transcript_to_srt(mapped), encoding='utf-8')
    report = {'schema_version': 'motiontalk.audio-preparation.v1', 'status': 'passed',
              'trim_breaths': trim_breaths, 'kept_breath_gap_seconds': keep_gap if trim_breaths == 'yes' else None,
              'selected_gaps': len(cuts), 'source_duration_seconds': duration, 'duration_seconds': expected,
              'sample_rate': SAMPLE_RATE, 'audio_sha256': digest, 'source': str(audio.resolve()), 'audio': str(master.resolve()),
              'subtitles': str((output / 'final.srt').resolve()), 'keep_intervals_samples': intervals,
              'deletions_samples': cuts, 'scope': 'Only reviewed breath gaps. No filler, mistake or retake removal.'}
    (output / 'audio-preparation-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report

def main() -> int:
    parser = argparse.ArgumentParser(description="Legacy low-level breath-edit library; not a production approval path")
    parser.parse_known_args()
    parser.error("Explicit migration required: use spoken_workflow.py init and obtain manuscript approval before render-audio")

if __name__ == '__main__':
    main()
