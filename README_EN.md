[简体中文](README.md) · **English**

# DraftCut

## Speak your ideas. Give them a screen.

Give your Agent a recording. DraftCut keeps your voice, tightens selected breath gaps, and brings your ideas to life with captions, diagrams and motion—a concise, polished spoken video.

**Start with one audio file.** No presenter footage, prepared subtitles or manual timeline layout required.

[Get started](#get-started) · [See the visual possibilities](#help-people-see-what-you-mean) · [How it works](#from-recording-to-finished-video)

![DraftCut turns a natural recording into a video with tighter pacing, captions and visual explanation. Original conceptual illustration.](assets/readme/draftcut-story-en.svg)

Our ambition: **100× less hands-on editing** for spoken videos, so you can spend more time expressing ideas. This goal has not yet been benchmarked.

## Still your voice. A tighter delivery.

Take your time. Find your words. The finished video can move a little faster.

Choose breath trimming and the Agent uses transcription and listening to tighten suitable pauses, keeping the ones that give your ideas room to land. Your spoken content and original voice stay; captions follow the edit. Choose no trimming to keep your original timing.

## Help people see what you mean

Explain a process with unfolding steps. Compare ideas side by side. Show a product as you describe it.

Bring materials and a reference video—or start with just your voice and let the Agent design around the content. Include presenter footage if you have it. Diagrams and animated text can tell the story on their own, too.

![An accelerated excerpt from the author's existing Vibe Working video, combining diagrams, presenter footage and a screen demonstration](assets/examples/vibe-working-6x.gif)

An existing creator video, shown **6× faster without sound**. [About the examples](docs/getting-started.md#examples-and-validation)

[Another diagram example](assets/examples/embodied-correction-6x.gif) · [More creator videos](https://www.xiaohongshu.com/user/profile/5b40fe744eacab72c9f480ef)

## Work in the Agent you already use

DraftCut is an Agent Skill for Agents with local file access, command execution, visual inspection and audio listening. The Agent reads the production method and uses local tools to make your video.

Recommended models: **Opus 5.5, ChatGPT 6 Astra and Kimi k3**.

## Get started

### 1. Set up once

You need **Python 3.10+, Node.js 22+, FFmpeg/ffprobe and a local full Google Chrome**. In a macOS/Linux terminal:

```bash
git clone https://github.com/PoetCoderJun/DraftCut.git
cd DraftCut
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
npm ci
```

Work with your Agent in this directory using this Python environment. You can also [install the Skill in your existing Agent](docs/getting-started.md#skill-installation).

Built-in transcription uses DashScope. Supply `DASHSCOPE_API_KEY` through secure environment configuration. **Audio is uploaded to that service and charges may apply; explicit authorization is required.** Keep keys out of prompts and Git. [Configuration guide](docs/getting-started.md#transcription-configuration-and-consent)

### 2. Give it a recording and a direction

Replace these paths with your real files, then send your Agent:

```text
Read SKILL.md in the current directory and use DraftCut.
Turn /absolute/path/my-recording.wav into a vertical spoken video.
Keep my voice and spoken content. Tighten breath gaps selected after listening.
Use key phrases and diagrams to support the explanation.
Show me the video director script for approval before production.
Write to /absolute/path/new-video-output, a new empty directory.
```

Add materials or a reference video if you have them. For an existing talking video, you can [use its original audio and footage](docs/getting-started.md#video-input).

### 3. Approve the visual story. Get your video.

The Agent works through the format, idea and style with you, then delivers a video director script. Once you approve it, the Agent continues through production, preview and MP4 export. The editable project stays available for revisions.

## From recording to finished video

![The workflow: record, select and tighten breath gaps, approve the video director script, produce and deliver the video.](assets/readme/draftcut-workflow-en.svg)

Prepare the voice, then shape the visual story. The director script brings composition, emphasis, assets and pacing together so you can see where the video is heading before production. Once approved, the Agent continues through production, review and delivery.

The current approval covers the video director script; an independent spoken-manuscript review is not yet integrated. See [what you review](docs/getting-started.md#what-you-review).

[Setup and usage](docs/getting-started.md) · [Engineering and validation](docs/harness-case-study.en.md) · [Integration and compatibility](docs/audio-first-migration.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

DraftCut was previously MotionTalk; existing project formats remain compatible. Licensed for non-commercial use under [CC BY-NC-SA 4.0](LICENSE.md). Commercial use requires prior written permission.

<!-- Compatibility anchors for previously published README links. -->
<a id="quickstart"></a>
<a id="creator-work"></a>
<a id="what-you-get"></a>
<a id="setup-and-data-path"></a>
<a id="checks-and-limitations"></a>
<a id="engineering-and-local-checks"></a>
<a id="compatibility-and-licenses"></a>
<a id="core-capabilities"></a>
<a id="development"></a>
<a id="first-run"></a>
<a id="install"></a>
<a id="just-tell-the-agent-what-you-want"></a>
<a id="license"></a>
<a id="reference-themes"></a>
<a id="参考主题"></a>
<a id="和-ai-说几句话就行"></a>
<a id="安装"></a>
<a id="开发验证"></a>
<a id="核心能力"></a>
<a id="检查与限制"></a>
<a id="第一次使用"></a>
<a id="许可"></a>
