# 视频导演脚本与第二道审核

先完成 [完整口播精剪](00-audio.md)，并通过第一道人工审核生成正式精炼音频。此后才在批准音频时间线上规划画面。

明确授权的隔离模拟 run 使用两次独立的模拟用户确认，流程和变更失效要求相同，但不冒称 owner 批准，见[测试说明](../docs/simulation-testing.md)。

逐步解决 layout、idea、materials、style、references；素材和参考片可选。依据内容组织论点、演示、比较与 MG 动画；不用每句标题卡代替解释。数字与事实必须有来源。

用户已经给过的素材和风格不要重复询问。其余可选偏好由 Agent 根据内容提出默认方案，合并进本次导演脚本确认；不用先连续问一串参数问题。

在工作项目写 `MG导演脚本.md` 与 `director-plan.json`。`source.audio/subtitles` 指向上一阶段返回版本目录的 `narration.wav/final.srt`，`duration_seconds` 取实际采样时长。结构例见 [plan.json](../examples/plan-validation/plan.json)。`workflow` 必须包含：

```json
{"schema":"draftcut.workflow.v2","project_dir":"项目绝对路径","director_script":"导演脚本绝对路径"}
```

`assets` 列出该计划要用的可选素材路径。`creative_brief` 解决版式、想法、素材和风格，`visual_direction/package_direction` 写具体表达，`render_spec` 指定画布与帧率。cues 在帧网格上从零连续覆盖至音频时长的帧舍入。不要设置 `approved=true`，它不是批准来源。

```bash
python3 <skill-root>/scripts/spoken_workflow.py director-review \
  --plan "$work/project/director-plan.json" --script "$work/project/MG导演脚本.md"
```

向用户交付返回的 `review.md`，其中包含完整脚本、计划、批准音频和素材摘要。**停在第二道门，等待用户对这版视频脚本明确签名批准**。第一道批准、无人值守措辞或 Agent 自审都不能代替这次批准。

```bash
python3 <skill-root>/scripts/validate_plan.py --plan "$work/project/director-plan.json"
```

该入口同时检查结构和两道当前签名。脚本、计划、素材变更使本次批准失效；口播稿变更则两次批准都需更新。批准后按 [制作](02-build.md) 连续执行。
