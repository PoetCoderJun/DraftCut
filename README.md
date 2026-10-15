**简体中文** · [English](README_EN.md)

# DraftCut

## 只管说，让好想法变成好视频。

把录音交给你的 Agent。DraftCut 保留你的声音，收紧多余气口，让字幕、图解和画面跟着你的表达展开，做成一条精炼、精美的口播视频。

**一段录音就能开始。** 不用先拍人物视频、做字幕，或在时间线上逐帧摆素材。

[开始制作](#开始制作) · [看看效果](#让观众看懂你在说什么) · [工作流程](#从开口到成片)

![DraftCut：自然说出的想法，经过气口整理和视觉设计，成为有字幕与图解的视频。原创示意图。](assets/readme/draftcut-story-zh.svg)

我们的目标：让口播视频的人工剪辑投入缩短 **100 倍**，把时间还给表达。这是产品愿景，尚无对照基准证明；实际耗时取决于素材、Agent、人工审核与渲染环境。

## 还是你的声音，表达更利落

说完一句，停下来想想下一句，很自然。成片可以更紧凑。

你选择是否剪气口，Agent 再结合转写和实际试听，筛选适合压缩的间隙。选中的气口默认收至 **0.25 秒**；有意义的思考与强调停顿留下。不剪，就保留原来的时间线。

声音来自你的原始录音。字幕跟着同一条剪辑时间线调整，重点再用图解、演示或动态文字展开。**当前自动化精剪范围是气口**；填充词、口误和重说的语义删除尚未集成，不能把“去冗余”理解为自动重写你的表达。

## 让观众看懂你在说什么

讲步骤，就让步骤逐个出现。讲差异，就把对象放在一起比较。讲产品，就让演示跟上讲解。你可以给一份素材、一条参考片，也可以只给录音，让 Agent 从内容设计画面。

| 你在讲什么 | 画面可以怎么表达 |
| --- | --- |
| 一个复杂的观点 | 图解跟着论证展开，突出关键关系 |
| 一套方法或操作 | 步骤、截图、录屏随讲解推进 |
| 一段个人表达 | 用重点文字与补充画面强化节奏；有人物素材时可加入人物构图 |

![作者既有 Vibe Working 成片的加速片段，展示图解、人物和录屏的配合](assets/examples/vibe-working-6x.gif)

作者既有成片片段，原片 00:39–01:27，**6 倍速、无声**。这是视觉表达参考，并非当前录音到成片流程的端到端验收。

[再看一个图解示例](assets/examples/embodied-correction-6x.gif) · [作者的更多视频](https://www.xiaohongshu.com/user/profile/5b40fe744eacab72c9f480ef)

## 在你习惯的 Agent 里使用

DraftCut 是一份 Agent Skill：让 Agent 读懂制作方法，再调用本地工具完成视频。只要它能读本地文件、运行命令，并实际查看画面和试听音频，就可以尝试接入；这不代表所有 Agent 都已测试通过。

项目作者推荐 **Opus 5.5、ChatGPT 6 Astra、Kimi k3**。这是创作模型的选择建议，不是兼容性认证；以你使用的平台实际可选模型和工具能力为准。只有聊天、没有文件和执行能力的环境，无法独立完成本地制作。

## 开始制作

### 1. 准备一次环境

需要 **Python 3.10+、Node.js 22+、FFmpeg/ffprobe 和本机完整 Google Chrome**。在 macOS/Linux 终端执行：

```bash
git clone https://github.com/PoetCoderJun/DraftCut.git
cd DraftCut
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
npm ci
```

让 Agent 在这个目录工作，使用这里的 Python 环境。也可以通过 [Skill 安装方式](docs/getting-started.md#skill-installation) 加入现有工具。

内置转写使用 DashScope。通过 Agent 的安全环境配置提供 `DASHSCOPE_API_KEY`；**音频会上传到该服务，可能产生费用，需要你明确授权**。不要把密钥写进提示词或提交到仓库。[配置、视频输入与常见问题](docs/getting-started.md)

### 2. 给它录音，说出你想要的效果

把路径换成你的真实文件，向 Agent 发送：

```text
读取当前目录的 SKILL.md，使用 DraftCut。
把 /绝对路径/我的录音.wav 做成一条竖屏口播视频。
保留我的声音，剪掉试听确认适合压缩的气口，不删除口播内容。
让重点和图解跟着讲解展开。先把视频导演脚本交给我审核，确认后再制作。
输出到 /绝对路径/本次视频输出（新的空目录）。
```

有素材或参考片就一并提供，没有也能开始。已有口播视频时，告诉 Agent 使用其中的原声，并明确是否把人物画面作为素材保留；[音频提取方法](docs/getting-started.md#video-input)见文档。

### 3. 确认画面怎么讲，收下成片

Agent 会与你逐步确定发布版式、想法和风格，交付可审核的视频导演脚本。批准后，继续完成字幕、视觉制作、预览检查和 MP4 导出。你拿到的是视频；可编辑工程保留，方便继续修改。

## 从开口到成片

![真实流程：录音输入、按选择整理气口、审核视频导演脚本、视觉制作并交付视频。](assets/readme/draftcut-workflow-zh.svg)

1. **给出录音。** 明确剪不剪气口；需要云转写时，确认上传与费用授权。
2. **整理声音。** 转写并复核内容；选择剪气口时逐段试听，只处理选中的间隙，同步字幕。
3. **审核视频脚本。** 你确认的是画面如何讲述：构图、重点、素材、节奏与对应的时间安排。默认审核对象是 `MG导演脚本.md` 及其配套计划。
4. **制作并检查。** Agent 实现视觉、连续预览、试听、导出和技术校验，再交付成片。

当前默认有一个人工创意审核点：**视频导演脚本**。气口选择与云服务授权是前置决定。录音内容复核属于音频准备，尚没有独立的“口播稿审核通过”门禁；因此当前不能描述为“两次审核已自动串联”。若你希望先看完整转写再继续，可在任务中明确要求 Agent 暂停等待确认。

## 再往里看

[安装与使用](docs/getting-started.md) · [工程原理与验证](docs/harness-case-study.md) · [集成范围与兼容](docs/audio-first-migration.md) · [第三方许可](THIRD_PARTY_NOTICES.md)

转写可能有错，剪口需要试听，画面需要连续观看；导出成功不等于内容、听感和视觉都已过关。100 倍目标不作为性能保证。当前验证与尚未覆盖的部分见工程文档。

DraftCut 原名 MotionTalk。已有项目格式保留兼容；安装入口和新 Skill 名称使用 `draftcut`。本项目按 [CC BY-NC-SA 4.0](LICENSE.md) 提供，限非商业使用；商业使用需事先取得书面授权，第三方素材遵循各自许可。

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
