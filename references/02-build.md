# 音频驱动的视觉制作

```bash
node <skill-root>/scripts/init_project.mjs --project-dir "$output_dir/hyperframes" --plan "$plan"
```

输入无需视频流。初始化主音频、内部字幕、可 seek 的 GSAP composition 和 project-state.json，只是 scaffold。按导演计划实际制作视觉故事，不把默认标题卡当成完整创作。

根画布直接位于 body，明确尺寸与时长；唯一主音频有唯一 id，可选视频/B-roll 默认静音避免音轨重复。DOM/SVG 字幕和图形保证中文可读性、留白与安全区。视觉随论证推进，数据必须真实，示意关系应明确标注。

时段用 clip/data-start/data-duration，Hyperframes 控制媒体；暂停动画注册到 window.__timelines.master，不自行播放/seek 媒体，不使用 CSS keyframes、系统时钟或网络字体。可选 [组件](06-modern-components.md) 安装前核对来源与许可。

```bash
node <skill-root>/scripts/hf.mjs lint "$output_dir/hyperframes"
node <skill-root>/scripts/hf.mjs check "$output_dir/hyperframes"
node <skill-root>/scripts/hf.mjs snapshot "$output_dir/hyperframes" --describe false
node <skill-root>/scripts/hf.mjs preview "$output_dir/hyperframes"
```

浏览器诊断使用 `hf.mjs` 入口，由它配置本机完整 Chrome（含 Apple Silicon wrapper）和默认 45 秒导航预算；不要求用户手工拼接浏览器环境变量。已有明确的 `PRODUCER_PAGE_NAVIGATION_TIMEOUT_MS` 设置会保留。`--timeout` 是底层诊断的初始化等待，不能替代导航预算。私有素材默认 `--describe false`，不调用外部图像分析。沙箱禁止回环服务或 Chrome 时沿正常工具授权路径处理，不通过增加超时掩盖权限失败。

连续预览覆盖开头、转场、密集内容和结尾；截图抽查不等于连续观看。核对字幕同步并实际试听；未执行就标 pending。完成制作后记录真实证据：

以上是生产验收。隔离模拟 run 完成实际视觉实现后，按[测试说明](../docs/simulation-testing.md)写 `test-ready`/`usability-only`，未测视听如实列出，不编造 continuous 证据。测试水印保留；不为本次测试另建展示 HTML 或自造操作平台。

```json
{"status":"ready","input":"audio","needs_visual_production":false,
 "visual_review":{"scope":"continuous","evidence":["preview-review.md"]}}
```

证据说明实际看过的时段、问题与修订，不能伪造。渲染器检查状态记录，不验证证据内容真假。随后按 [交付](03-deliver.md) 继续。

## 预览和输出一致

在 GSAP 时间线上为场景与字幕明确设置开始／结束显隐，不依赖 Studio 与导出器恰好用同一种方式解释 clip。使用专用 class 或属性选择器作为动画目标；锁定 CLI 会注入 `data-hf-id`，某些 ID 目标改写在 Studio 中可能找不到原 DOM，专用 class 能避免该问题。所有显隐和运动都必须可 seek。

`main-audio` 必须是唯一有声元素，从零播放批准 WAV，unity gain、原速；视觉视频必须 muted。字幕保留 `caption-0` 等稳定 ID、批准文字与时间，可在内部加入强调 span。门禁会检查静态 DOM 文本和时间，批准 WAV/SRT 文件必须保持字节一致；实际连续预览仍需确认运行时效果。

音频样本时长经常不在视频帧网格上。根画布和末场视觉应覆盖 `ceil(audio_seconds × fps)` 个输出帧，沿用 scaffold 的 `visualFrameEnd` 边界，避免把末场在向下取整的时刻隐藏。只扩展末帧的视觉覆盖，不改批准音频、字幕或计划的样本时间。特别核对实际最后一帧，较早的结尾截图不能证明末帧正常。

锁定版本 Studio 若出现空画布等预览问题，可用同工程的本机连续预览替代，不升级运行时：

```bash
python3 <skill-root>/scripts/preview_project.py --project-dir "$work/project/hyperframes" --port 3042
```

在用户本机浏览器打开打印的回环 URL，点击播放，完整观察字幕、转场和结尾。该查看器只驱动同一暂停 GSAP 时间线、clip 时段与批准原声音轨，不签发任何批准，也不替换导出器。预览结束停止本次服务；如仍无法实际观看，保持 pending，不标 ready。
