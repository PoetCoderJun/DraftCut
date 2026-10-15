---
name: draftcut
description: Turn an audio recording into a complete social video with internal ASR, explicitly chosen breath-gap editing, a progressive creative brief and audio-driven Hyperframes production. Optional materials and reference videos are welcome; user video and SRT are not required.
---

# DraftCut

唯一必需的用户素材是音频文件；素材文件夹和参考成片可选。内部生成转写、逐词时间戳和匹配 SRT，不要求用户先准备视频或字幕。目标是完整 MP4、导演计划与检查报告，初始化模板本身不算成片。

## 先确认气口选择

用户尚未明确时，必须先问：**“要智能剪气口吗？剪的话，我会试听筛选气口，默认将选中的间隙压到 0.25 秒；不剪就保持原音频时间线。”** 不默认、不替用户决定。已有明确选择时记录并继续，不重复询问。

- 不剪：只转写、生成内部 SRT，保留原时间线。48 kHz WAV 格式归一化不是剪辑。
- 剪：结合逐词时间戳与实际试听判断气口。候选词间空隙不是气口检测结果；保留思考、强调和自然节奏。只批准确认的气口，默认保留 0.25 秒，短于目标的不动。
- 无法试听时不伪称听过，不自动批准候选，明确气口审核待完成。
- 气口授权不包含填充词、口误、重说或内容删除；另有明确指示才能做。
- 内置云 ASR 会上传音频且可能收费，调用前必须有明确授权。`--allow-cloud-asr` 是门禁，不是授权来源；不得擅自上传私人或公司资料。

读取 [references/00-audio.md](references/00-audio.md)。目录从音频名推导，Agent 管理内部路径，不向用户索要项目名、SRT 或 CLI 参数。

## 渐进创意沟通

利用已有信息，逐步解决发布场景与版式、核心创意、可选素材/B-roll、视觉风格与可选参考成片；避免一次塞满问卷。已有答案不重复问，用户授权自行决定时记录假设。参考可访问则分析构图、节奏、信息推进和动效；无法访问如实说明。参考用于理解表达，不下载、复制或重用未经许可的画面、音乐或字体。素材与参考都不是必需品；没有人物视频就用全屏视觉叙事。

## 规划、制作、交付

1. 按 [规划](references/01-plan.md)，在准备后的最终音频时间线上生成导演脚本与机器计划。通常批准具体计划后制作；明确无人值守授权已覆盖时记录原文并继续，不重复请求审批。气口未回答仍须问。
2. 批准后按 [制作](references/02-build.md) 创建 HTML/CSS/GSAP 工程并实现内容驱动的视觉故事，随后同次工作按 [交付](references/03-deliver.md) 验证、导出与交付。
3. 画面持续推进有用信息，重点跟随论证；只用有来源的数据，不能靠静止标题加字幕宣称完成创意制作。

技术检查只证明结构、时间线与媒体格式；视觉语义需要连续预览，音质需要实际试听。分别报告，未做的检查标 pending。批准是可审查状态，不是签名；超出既有授权的新输入、时间线或创意方向需重新规划，已授权修订直接执行。

## Hyperframes 契约

使用锁定的 Hyperframes 0.8.30、GSAP 3.14.2（Node >=22），Python 依赖见 requirements.txt；不自动升级或安装来源不明组件。依赖安装由明确环境授权决定。

主入口 output_dir/hyperframes/index.html：body 直属的定尺寸根 composition、单一主音频 assets/narration.wav、可编辑 DOM/SVG 字幕与图形。每个媒体有唯一 id 和明确时段，框架控制播放。GSAP 时间线暂停、可 seek，注册到 window.__timelines.master；不依赖系统时钟、随机状态、CSS 动画或远程字体。

init_project.mjs 创建 **scaffold**，需实际制作后记录连续预览证据并标记 ready 才可 production 导出。--purpose smoke 仅用于标注为合成的技术测试，不能代替创作者成片。默认单 worker、本机完整 Chrome、硬件 H.264；可明确选择 --encoding software，不静默切换。

入口：transcribe_audio.py、prepare_audio.py、validate_plan.py、init_project.mjs、hf.mjs、render_master.mjs、validate_master.mjs。可选方向见 [参考](references/04-reference-theme-prompt.md)。仅在用户要求倍速、响度或失真修复时读 [音频母带](references/05-social-loudness.md)，同步重映射字幕与视觉。可选组件见 [组件](references/06-modern-components.md)，核对来源与许可后安装。

保留原音频、已有项目和旧版本，在新空目录生成内部产物。已有项目格式与集成依赖保留，兼容说明见 [迁移文档](docs/audio-first-migration.md)。不自动发布或上传。遵守 [LICENSE.md](LICENSE.md) 非商业条款，商业使用须事先书面授权；第三方材料适用自身许可。
