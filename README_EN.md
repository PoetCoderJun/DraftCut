[简体中文](README.md) · **English**

# DraftCut

## Speak your ideas. Give them a screen.

Give your Agent a recording. DraftCut keeps your voice, refines fillers, mistakes and retakes, and brings your ideas to life with captions, diagrams and motion—a concise, polished spoken video.

**Start with one audio file.** No presenter footage, prepared subtitles or manual timeline layout required.

[Get started](#get-started) · [See the visual possibilities](#help-people-see-what-you-mean) · [How it works](#from-recording-to-finished-video)

![DraftCut: speak naturally, approve a refined edit of your original voice, and turn it into a polished video with visual explanations. Original static frames.](https://raw.githubusercontent.com/PoetCoderJun/DraftCut/cc359ed78804c0de897f394e2c3bf5d4857508a6/assets/readme/draftcut-story-en.svg)

Our ambition: **100× less hands-on editing** for spoken videos, so you can spend more time expressing ideas. This goal has not yet been benchmarked.

## Still your voice. A tighter delivery.

Take your time. Find your words. The finished video can move a little faster.

The Agent reads and listens through the full recording to refine fillers, mistakes, corrections, retakes and pauses, preserving your meaning and deliberate emphasis. Review the refined manuscript and the reasons for each edit first. Once you approve it, the original voice is cut to that exact version and captions follow the sound.

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
Keep my voice. Refine fillers, mistakes, retakes and redundant pauses.
Show me the spoken manuscript and edit reasons for approval before creating the refined audio.
Use key phrases and diagrams to support the explanation.
Show me the video director script for approval before production.
Write to /absolute/path/new-video-output, a new empty directory.
```

Add materials or a reference video if you have them. For an existing talking video, you can [use its original audio and footage](docs/getting-started.md#video-input).

### 3. Approve the visual story. Get your video.

Review the spoken manuscript, then the video director script. After both approvals, the Agent continues through production, preview and MP4 export. The editable project stays available for revisions. [How approval works](docs/approvals.md)

## From recording to finished video

![Review the spoken edits, approve the visual script with scenes and captions, then produce the finished video.](https://raw.githubusercontent.com/PoetCoderJun/DraftCut/cc359ed78804c0de897f394e2c3bf5d4857508a6/assets/readme/draftcut-workflow-en.svg)

Prepare the voice, then shape the visual story. The director script brings composition, emphasis, assets and pacing together so you can see where the video is heading before production. Once approved, the Agent continues through production, review and delivery.

**Approve the spoken manuscript → approve the video script → get the video.** Each approval covers a specific revision; content changes require a new review. See [what you review](docs/getting-started.md#what-you-review).

[Setup and usage](docs/getting-started.md) · [Engineering and validation](docs/harness-case-study.en.md) · [Integration and compatibility](docs/audio-first-migration.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

DraftCut was previously MotionTalk. Existing projects need [migration and fresh approvals](docs/audio-first-migration.md); keep their original materials and editable files. Licensed for non-commercial use under [CC BY-NC-SA 4.0](LICENSE.md). Commercial use requires prior written permission.

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
