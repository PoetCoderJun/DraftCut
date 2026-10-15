# DraftCut: an inspectable Agent Harness case study

[中文](harness-case-study.md) · [Project](../README.md)

Turning audio into a social video combines open creative judgment with mechanical constraints. DraftCut separates them so reviewers can inspect both the decisions and the code.

| Stage | Reviewable record | Mechanical boundary |
| --- | --- | --- |
| User intent | Explicit breath yes/no, progressive creative brief, optional materials/references | ASR wrapper requires a choice and a separate cloud-consent flag |
| Audio preparation | Source SHA-256, listening-approved breath intervals, kept/deleted sample ranges | Reject wrong-source reviews, word overlap and overlapping cuts; remap words/SRT using the same deletion map |
| Planning | Director script and approved machine plan | Positive dimensions/fps/duration, resolved brief, nonempty visual prompts, frame-grid contiguous cues |
| Initialization | Audio-first editable composition, status=scaffold | Require decodable audio and matching duration; no presenter video; refuse nonempty project directories |
| Production | Content-aware visuals and continuous preview evidence | Production renderer requires ready status and existing recorded evidence; smoke mode is explicitly synthetic |
| Delivery | Render log/metrics, technical report, separate visual/listening review | Compare dimensions, fps, video/audio duration, H.264/AAC and one-MP4 delivery directory |

## Determinism and judgment

[prepare_audio.py](../scripts/prepare_audio.py) proposes unclassified word gaps, never auto-approved breaths. An Agent must listen and select suitable intervals. The script keeps 0.25 seconds by default only in approved breath gaps; no-trim keeps the timeline. It blocks cuts overlapping word timestamps, but inaccurate ASR timings can still expose speech. It cannot establish natural pacing or sound quality. SRT timestamps are rounded to milliseconds after sample-based mapping.

[validate_plan.py](../scripts/validate_plan.py) checks plan structure and cue timing, not user identity, approval revision binding, media existence or visual meaning. [init_project.mjs](../scripts/init_project.mjs) then checks audio existence/decoding, duration and subtitle bounds. The initializer is a scaffold, not a complete creative result.

[render_master.mjs](../scripts/render_master.mjs) reads Agent-authored production state and checks recorded evidence paths. It does not inspect evidence pixels or prove the review actually occurred. Hardware/software selection is explicit; dependency versions, worker count and seekable timelines make execution inspectable, but this does not promise byte-identical output across hardware.

[validate_master.mjs](../scripts/validate_master.mjs) checks output metadata with a three-frame timing tolerance and audio presence/duration. Its report explicitly says scope=technical and visual_review=not_assessed_by_this_validator. Visual understanding and listening remain separate, truthful review tasks. No signed approvals or whole-project hash binding are implemented.

## Reproduce

```bash
python3 examples/plan-validation/run.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s scripts/tests -v
node --test tests/*.test.mjs
python3 examples/audio-only-smoke/run.py --output-dir /tmp/draftcut-fresh-smoke --render
```

The last command uses a generated tone and authored timestamps, no cloud ASR or private input. It requires pinned runtime dependencies, FFmpeg and local Chrome. It verifies that an audio-only composition can render, not creative quality, real ASR accuracy, natural breath selection or a cost/time benchmark. See [migration notes](audio-first-migration.md).

The transferable pattern is a clear decision record, narrow deterministic gates and separately evaluated Agent judgment. It can inform exploration in Work, Robotics or Finance; this media implementation does not establish enterprise deployments, robotics capability, financial performance or ROI.

[CC BY-NC-SA 4.0](../LICENSE.md) remains unchanged; commercial use needs prior written permission. Third-party materials retain their rights.
