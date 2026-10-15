[简体中文](README.md) · **English**

# DraftCut

## Speak your ideas. Give them a screen.

Give your Agent a recording. DraftCut keeps your voice, refines fillers, mistakes and retakes, and brings your ideas to life with captions, diagrams and motion—a concise, polished spoken video.

**Start with one audio file.** No presenter footage, prepared subtitles or manual timeline layout required.

[Get started](#get-started) · [See the visual possibilities](#help-people-see-what-you-mean)

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

### 1. Send the repository link to your Agent

Send this to an Agent with local file access and command execution:

```text
Read https://github.com/PoetCoderJun/DraftCut and install and configure DraftCut for me.
Follow its Agent setup guide: inspect the environment, reuse healthy dependencies,
install what is missing, and run the health checks.
Report the actual results, then use DraftCut to help me make a spoken video.
If system access, credentials, or cloud upload and paid-service consent is needed,
request it through a secure route.
```

The Agent follows the repository's [installation and health-check guide](docs/agent-bootstrap.md), handles setup, and reports what actually works. [Configure the API key once](docs/configuration.md); DraftCut reuses it across projects. Keep credentials out of prompts and Git. Built-in cloud transcription uploads audio and may incur charges, so it still needs your explicit consent.

### 2. Give it a recording and a direction

Replace these paths with your real files, then send your Agent:

```text
Please use the DraftCut Skill to turn /absolute/path/my-recording.wav into a video.
The style and feel I want is…
```

Add materials or a reference video if you have them. For an existing talking video, you can [use its original audio and footage](docs/getting-started.md#video-input).

### 3. Approve the visual story. Get your video.

Review the spoken manuscript, then the video director script. After both approvals, the Agent continues through production, preview and MP4 export. The editable project stays available for revisions. [How approval works](docs/approvals.md)

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
