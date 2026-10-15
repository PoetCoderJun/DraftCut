# Audio-only smoke / 纯音频渲染验证

From the repository root, after installing the pinned dependencies and local Chrome:

```bash
python3 examples/audio-only-smoke/run.py --output-dir /tmp/draftcut-new-smoke --render
```

Creates a newly synthesized two-second tone/silence recording, authored timestamp fixture, prepared WAV/SRT and a Hyperframes project with **no video element**. Lints, explicitly renders in software smoke mode, then checks H.264/AAC, dimensions, frame rate and both media durations. Choose a new empty directory. Without `--render`, it only prepares, initializes and lints.

No cloud ASR, private recordings, model calls or paid service is used. Approval fields simulate a test, not a user's production approval. The composition remains a scaffold; this does not establish creative quality, natural breath editing, listening review or benchmark performance. Local Chrome/rendering permissions may be needed for the temporary local server.

使用新空目录。输入为现场合成声音与作者编写时间戳，不是真实 ASR；没有人物视频。软件 smoke 导出专用于技术验证，不可当作视觉创作或试听验收。

Use `--trim-breaths yes` to test a fixture-defined 1-second gap compressed to 0.25 seconds and a 1.25-second output audio timeline. This approved synthetic gap is authored for the test; it does not simulate actual listening or automatic breath detection.
