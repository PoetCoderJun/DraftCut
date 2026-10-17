# 导出与交付

```bash
node <skill-root>/scripts/render_master.mjs --project-dir "$output_dir/hyperframes" \
  --plan "$plan" --output "$output_dir/final/video.mp4"
node <skill-root>/scripts/validate_master.mjs --plan "$plan" \
  --final "$output_dir/final/video.mp4" --output-dir "$output_dir"
```

production 导出要求 ready 和连续预览证据。默认本机完整 Chrome、单 worker、硬件 H.264；环境不支持时明确使用 --encoding software，不静默替换。不能自动下载浏览器或升级运行时。--purpose smoke 仅用于标为合成的技术测试，不绕过创作者视频的制作。

用户明确授权且有独立 run 清单的模拟用户测试，必须用 `--purpose simulation`、run 内 `TEST-*.mp4` 和测试水印，见[测试说明](../docs/simulation-testing.md)。不能用 production 或 smoke 接受模拟批准；报告只作交互与技术链路证据。

final/ 仅含最终 MP4，日志、计划、字幕和报告在工作目录。校验批准状态、尺寸/帧率、视频和音频时长、H.264/AAC、单文件交付；时长容差为三帧，不是感知同步证明。连续观看覆盖开头/中段/尾段，核对字幕与论点；试听可选，未试听如实记录，不构成出片门槛。

从导出的 MP4 精确提取实际最后一帧（帧号 `nb_frames - 1`），检查批准结尾仍可见，模拟导出还须可见测试水印；不能只看 `duration - 0.1s`。最后一帧空白即修正同工程视觉覆盖并重新渲染，保留失败版本，禁止把重封装或元数据通过当作画面已修复。

quality-report.v1.json scope=technical；视觉与听感单独记录，没做就 pending，不把技术通过写成创意或音质已确认。交付视频、导演计划、准备报告、技术报告、预览/试听结论和真实限制。失败保留日志，不以假样例替代。

不自动上传 GitHub、Library 或视频平台；[非商业许可](../LICENSE.md) 与商业事先书面授权要求保留。

## v2 发布门禁

初始化、正式／合成导出和交付检查都会重验两道签名链。工程目录固定为该工作项目的 `hyperframes/`；不能从另一个工程借用批准。导出前检查唯一原声音轨、DOM 字幕内容／时间和批准素材；导出后比较 AAC 解码波形与批准 WAV，mono→stereo 显式复制声道，避免隐式下混增益干扰。

`--purpose smoke` 仅接受经过两次 fixture 模拟批准的已知合成 PCM／词表。给真实录音加 `example_only` 标签、设置旧 approved 字段或拿旧审核文件重试都不能通过。导出临时文件先完成检查，再复制到交付目录；日志和导出批准记录保存在工程内。
