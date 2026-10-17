**简体中文** · [English](README_EN.md)

# DraftCut

## 只管说，让好想法变成好视频。

把录音交给你的 Agent。DraftCut 保留你的声音，整理口头禅、口误和重说，让字幕、图解和画面跟着你的表达展开，做成一条精炼、精美的口播视频。

**一段录音就能开始。** 不用先拍人物视频、做字幕，或在时间线上逐帧摆素材。

[开始制作](#开始制作) · [看看效果](#让观众看懂你在说什么)

![DraftCut：自然说话，经口播稿审核精炼为原声音频，再用图解、字幕和章节设计成精美视频。原创静态代表帧。](https://raw.githubusercontent.com/PoetCoderJun/DraftCut/cc359ed78804c0de897f394e2c3bf5d4857508a6/assets/readme/draftcut-story-zh.svg)

我们的愿景：让口播视频的人工剪辑投入缩短 **100 倍**，把时间还给表达。这个目标尚未经基准验证。

## 还是你的声音，表达更利落

录音时，你可以慢慢想、自然说。成片时，让讲述更紧凑。

Agent 通读完整逐词转写与上下文，整理口头禅、口误、改口、冗余重说和停顿，留下完整自然的表达、思考与强调的节奏。先在当前命令行／对话看完整精炼口播稿与修改依据；明确批准后自动交付干净成片与旁挂字幕，不要求再发渲染指令或终端签名。试听可选；包装另外审核导演脚本。你确认后，再把原声剪成同一版本，字幕跟着声音走。

## 让观众看懂你在说什么

讲步骤，就让步骤逐个出现。讲差异，就把对象放在一起比较。讲产品，就让演示跟上讲解。

你可以给一份素材、一条参考片，也可以只给录音，让 Agent 从内容设计画面。有人物素材，就把人物放进故事；没有，也能用图解和动态文字讲清楚。

![作者既有 Vibe Working 成片的加速片段，展示图解、人物和录屏的配合](assets/examples/vibe-working-6x.gif)

作者既有成片片段，**6 倍速、无声**。[示例说明](docs/getting-started.md#examples-and-validation)

[再看一个图解示例](assets/examples/embodied-correction-6x.gif) · [作者的更多视频](https://www.xiaohongshu.com/user/profile/5b40fe744eacab72c9f480ef)

## 在你习惯的 Agent 里使用

DraftCut 是一份 Agent Skill，支持具备本地文件读写、命令执行和视听能力的 Agent。让它读懂制作方法，再调用本地工具完成视频。

推荐模型：**Opus 5.5、ChatGPT 6 Astra、Kimi k3**。

## 开始制作

### 1. 把仓库链接发给 Agent

把这段话发给具备本地文件与命令能力的 Agent：

```text
请读取 https://github.com/PoetCoderJun/DraftCut，为我安装配置 DraftCut。
按仓库的 Agent 安装说明检查环境，复用已有依赖，补齐缺失项并执行健康检查。
完成后告诉我检查结果，再使用 DraftCut 帮我制作口播视频。
如需系统权限、密钥或云服务上传与费用授权，请通过安全方式提示我。
```

Agent 会读取仓库内的[安装与健康检查说明](docs/agent-bootstrap.md)，负责配置并报告实际结果。API key [首次安全配置后自动复用](docs/configuration.md)，不粘贴到提示词或写进仓库。内置云转写需要上传音频且可能收费，使用前仍须你明确授权。

### 2. 给它录音，说出你想要的效果

把路径换成你的真实文件，向 Agent 发送：

```text
请使用 DraftCut 的 Skill，把 /绝对路径/我的录音.wav 做成一个视频。
我想要的样式和风格是……
```

有素材或参考片就一并提供。已有口播视频，也可以[使用其中的原声和画面](docs/getting-started.md#video-input)。

### 3. 确认画面怎么讲，收下成片

先审核口播稿，再审核视频导演脚本。两次确认后，Agent 继续制作、预览和导出 MP4。可编辑工程保留，方便继续修改。[审核操作](docs/approvals.md)

[安装与使用](docs/getting-started.md) · [工程与验证](docs/harness-case-study.md) · [集成范围与兼容](docs/audio-first-migration.md) · [第三方许可](THIRD_PARTY_NOTICES.md)

DraftCut 原名 MotionTalk；旧项目需[迁移后重新审核](docs/audio-first-migration.md)，原有素材与工程可保留。按 [CC BY-NC-SA 4.0](LICENSE.md) 提供，限非商业使用；商业使用需事先取得书面授权。

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
