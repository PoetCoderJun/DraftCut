# Derived from clean-talking-video render_edit.py, MIT, PoetCoderJun 2026.
# Pure timeline/subtitle helpers only; no standalone rendering/approval bypass.
from __future__ import annotations

import argparse
import json
import math
import platform
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Optional


TOLERANCE = 0.000001


def report_progress(step: int, total: int, message: str) -> None:
    """Write a compact progress update without polluting stdout JSON."""
    print(f"[{step}/{total}] {message}", file=sys.stderr, flush=True)


def number(value: float) -> float:
    return round(float(value), 6)


def number_text(value: float) -> str:
    return f"{float(value):.9f}".rstrip("0").rstrip(".") or "0"


def normalize_ranges(
    ranges: list[dict[str, Any]],
    *,
    label: str,
    source_duration: float,
) -> list[tuple[float, float]]:
    normalized: list[tuple[float, float]] = []
    for index, item in enumerate(ranges):
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{label} {index} has invalid start/end") from exc
        if not all(math.isfinite(value) for value in (start, end)):
            raise ValueError(f"{label} {index} contains a non-finite time")
        if start < 0 or end <= start or end > source_duration + TOLERANCE:
            raise ValueError(
                f"{label} {index} must satisfy 0 <= start < end <= source duration"
            )
        normalized.append((max(0.0, start), min(source_duration, end)))
    normalized.sort()
    return normalized


def validate_non_overlapping(ranges: list[tuple[float, float]], *, label: str) -> None:
    previous_end = -math.inf
    for index, (start, end) in enumerate(ranges):
        if start < previous_end - TOLERANCE:
            raise ValueError(f"{label} {index} overlaps the previous interval")
        previous_end = max(previous_end, end)


def merge_ranges(ranges: list[tuple[float, float]]) -> list[tuple[float, float]]:
    merged: list[list[float]] = []
    for start, end in ranges:
        if not merged or start > merged[-1][1] + TOLERANCE:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def finalize_timeline(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("version") != "talking-head-edit-plan.v1":
        raise ValueError("unsupported edit plan version")
    try:
        source_duration = float(plan["source_duration_seconds"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("source_duration_seconds must be positive") from exc
    if not math.isfinite(source_duration) or source_duration <= 0:
        raise ValueError("source_duration_seconds must be positive")

    base = normalize_ranges(
        plan.get("base_keep_segments", []),
        label="base_keep_segment",
        source_duration=source_duration,
    )
    if not base:
        raise ValueError("base_keep_segments must not be empty")
    validate_non_overlapping(base, label="base_keep_segment")
    deletions = merge_ranges(
        normalize_ranges(
            plan.get("delete_ranges", []),
            label="delete_range",
            source_duration=source_duration,
        )
    )

    kept: list[tuple[float, float]] = []
    for base_start, base_end in base:
        cursor = base_start
        for delete_start, delete_end in deletions:
            if delete_end <= cursor + TOLERANCE:
                continue
            if delete_start >= base_end - TOLERANCE:
                break
            if delete_start > cursor + TOLERANCE:
                kept.append((cursor, min(delete_start, base_end)))
            cursor = max(cursor, delete_end)
            if cursor >= base_end - TOLERANCE:
                break
        if cursor < base_end - TOLERANCE:
            kept.append((cursor, base_end))
    if not kept:
        raise ValueError("edit plan deletes the entire video")

    segments: list[dict[str, float]] = []
    out_start = 0.0
    for start, end in kept:
        segments.append(
            {
                "start": number(start),
                "end": number(end),
                "out_start": number(out_start),
            }
        )
        out_start += end - start
    return {
        "version": "talking-head-edit-timeline.v1",
        "source_duration_seconds": number(source_duration),
        "cut_duration_seconds": number(out_start),
        "segments": segments,
    }


def format_srt_timestamp(value: float) -> str:
    total_ms = max(0, round(float(value) * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def map_subtitle(
    subtitle: dict[str, Any],
    segments: list[dict[str, float]],
) -> Optional[tuple[float, float]]:
    source_start = float(subtitle["source_start"])
    source_end = float(subtitle["source_end"])
    if source_end <= source_start:
        raise ValueError(f"subtitle {subtitle.get('id')} has invalid source times")
    mapped: list[tuple[float, float]] = []
    for segment in segments:
        overlap_start = max(source_start, float(segment["start"]))
        overlap_end = min(source_end, float(segment["end"]))
        if overlap_end <= overlap_start + TOLERANCE:
            continue
        mapped.append(
            (
                float(segment["out_start"]) + overlap_start - float(segment["start"]),
                float(segment["out_start"]) + overlap_end - float(segment["start"]),
            )
        )
    if not mapped:
        return None
    return mapped[0][0], mapped[-1][1]


def build_srt(
    subtitles: list[dict[str, Any]],
    segments: list[dict[str, float]],
) -> str:
    blocks: list[str] = []
    for subtitle in subtitles:
        text = str(subtitle.get("text", "")).strip()
        if not text:
            continue
        mapped = map_subtitle(subtitle, segments)
        if mapped is None:
            continue
        start, end = mapped
        if end <= start + TOLERANCE:
            continue
        blocks.append(
            f"{len(blocks) + 1}\n"
            f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}\n"
            f"{text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")
