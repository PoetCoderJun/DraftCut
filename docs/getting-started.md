# DraftCut 安装与使用 / Setup and usage

[中文首页](../README.md) · [English overview](../README_EN.md)

## Environment

- Python 3.10+, Node.js 22+, FFmpeg/ffprobe and a full local Google Chrome.
- Apple Silicon uses native ARM64 Node and Chrome. Dependencies pin Hyperframes 0.8.30 and GSAP 3.14.2.
- The Agent needs local file/command access, visual inspection and actual audio listening. Model names alone do not establish these capabilities.

The README's clone + virtual-environment commands are the reproducible macOS/Linux path. On Windows use `py -3 -m venv .venv`, then `.venv\Scripts\Activate.ps1` in PowerShell; install FFmpeg and Chrome and make their executables available. Windows has not been verified in this documentation pass.

Activate the virtual environment in the shell that launches your Agent, or instruct it to use `.venv/bin/python` for the Python scripts. A fresh terminal does not inherit an earlier activation. `npm ci` installs the exact lockfile; no global renderer installation is needed.

## Skill installation

For an Agent supported by the Skills installer:

```bash
npx skills add PoetCoderJun/DraftCut --skill draftcut
```

Choose your Agent and installation scope in the installer. In the installed Skill directory, create/activate a Python virtual environment, run `python3 -m pip install -r requirements.txt` and `npm ci`, as in the README. Then use `$draftcut`, or ask the Agent to read that directory's `SKILL.md` directly if it does not support named Skill invocation.

The repository rename does not update an already installed `$motiontalk`. Keep existing projects, install the new Skill, and explicitly select `$draftcut`; do not assume an old local checkout contains the current audio workflow. See [compatibility](audio-first-migration.md#draftcut-compatibility).

## Transcription configuration and consent

The current built-in path is DashScope cloud ASR, not offline transcription. Obtain a service key with access to the configured model, and provide it through the execution environment's secret settings. Keep the key out of prompts, recordings, logs and Git. The scripts read environment variables; they do **not** automatically load `.env` files.

| Variable | Current behavior |
| --- | --- |
| `DASHSCOPE_API_KEY` | Required credential; legacy `DASHSCOPE_ASR_API_KEY` is also accepted |
| `DASHSCOPE_BASE_URL` | Defaults to `https://dashscope.aliyuncs.com`; legacy `DASHSCOPE_ASR_BASE_URL` takes precedence when set |
| `DASHSCOPE_ASR_MODEL` | Defaults to `qwen3-asr-flash-filetrans` in the vendored adapter |

Verify the endpoint, region, model access and applicable pricing in your service account. The configuration above describes the adapter, not a guarantee of service availability.

Before the Agent runs ASR, explicitly authorize uploading the chosen recording and any service charges. `--allow-cloud-asr` records that decision in the command; it is not permission on its own. The adapter uploads an audio proxy, submits an asynchronous job, polls it and downloads the result. Local rendering does not make the whole workflow local; your Agent platform's data handling also applies. If you decline upload, the Agent can discuss the visual idea, but the built-in transcription step cannot proceed.

The public workflow and exact commands live in [audio preparation](../references/00-audio.md). Source audio is preserved, and every run needs a new empty output directory.

## Video input

The production timeline is audio-first. If you have a talking video, authorize extracting its original audio and keep the video as an optional visual asset. For example, from a directory containing `my-talk.mp4`:

```bash
ffmpeg -n -i my-talk.mp4 -vn -c:a pcm_s24le -ar 48000 my-talk-audio.wav
```

Pass `my-talk-audio.wav` to DraftCut. `-n` refuses to overwrite an existing file. If you want the speaker to remain visible, provide `my-talk.mp4` as a material and make that intent explicit. Trimming audio changes its timeline: the Agent must align any original video to the same cuts; merely placing the untouched video underneath edited audio is not lip-sync. The current preparation script does not automatically recut presenter footage.

## What you review

| Stage | Actual review / decision |
| --- | --- |
| Input | User chooses breath trimming yes/no; separately authorizes cloud upload/charges |
| Audio preparation | Agent checks transcript content and listens to candidate gaps; only reviewed breath gaps are edited |
| Director plan | User normally approves `MG导演脚本.md` and `mg-placement-plan.v1.json`, covering the proposed visuals and timing |
| Production | Agent previews continuously, listens and runs technical validation; no new default user approval gate |

An explicit unattended-production authorization can cover the director plan; record the user's actual instruction. It does not answer an unspecified breath-trimming choice or independently authorize cloud upload. An independent full-transcript approval gate and semantic filler/retake removal are not implemented. If requested, the Agent should pause for transcript review as a task-specific instruction, not pretend a code-enforced gate exists.

## Delivery and troubleshooting

The user-facing result is `final/video.mp4`. Working audio, matching subtitles, director plan, editable HTML/CSS/GSAP composition and review reports remain in the project directory for inspection and revision. They are not separate finished products.

- **No key or consent:** configure the service and authorize the chosen source before ASR; do not silently switch providers.
- **No word timings or no listening capability:** do not auto-approve breath candidates; preserve timing or resolve the missing review.
- **Misheard words or rough cuts:** correct timings/content against the source and listen again before planning visuals.
- **Chrome/hardware unavailable:** provide the real full Chrome path; choose `--encoding software` explicitly if needed. Do not silently download a browser or change encoding mode.
- **“Complete the approved visual production”:** the initializer only created a scaffold. Finish the visuals and record real continuous-review evidence before production export.

See [the engineering case study](harness-case-study.en.md) for checks and limits. A technical pass does not certify creative quality, natural speech or perceptual synchronization.

## Local verification

From the repository root after dependency setup:

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s scripts/tests -v
node --test tests/*.test.mjs
python3 examples/plan-validation/run.py
```

These use synthetic fixtures and mocked service results, not private recordings or live cloud models. Optional [audio-only smoke rendering](../examples/audio-only-smoke/README.md) checks the renderer, not an end-to-end creator project or the 100× aspiration.

The README SVGs are original, editable vector illustrations authored for DraftCut. Their dialogues, waveforms and layouts are schematic, not screenshots, measured before/after results or a product UI. They contain no external fonts, scripts or linked assets. Existing creator GIFs are separately labeled as prior finished work.
