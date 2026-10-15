# 隔离的模拟用户交互测试

这是明确授权的测试工具，不是创作者视频的生产批准入口。执行 Agent 仍只接收简短素材/风格请求，从 SKILL 学习流程；测试环境只提供素材缓存、run 清单和安全边界，不把流程步骤预写进用户请求。

## 测试控制器（不交给普通使用者）

在新空目录创建 test run：

```bash
python3 scripts/simulation.py create --source /path/source.MOV --run-dir /path/new-test-run
```

私有测试身份保存在该 run 的控制器文件，绝不写入 `~/.config/draftcut`。向执行者提供生成的 `run.json` 路径；项目必须在该 run 的 `projects/` 下。执行者提出第一道/第二道确认时，测试控制器扮演普通用户自然回复，并在内部记录同一句回复：

```bash
python3 scripts/simulation.py approve --request /path/current/request.json --reply '这版可以，继续吧。'
```

控制器必须先读执行者本轮提案，不能提前批准尚未出现的请求，也不能让执行者代替模拟用户自批。签名绑定当前请求、stage、项目、generation 和 run。修改后旧回执不能继续用。

## 执行 Agent

执行同一口播工作流，仅在导入时传入环境提供的清单：

```bash
python3 scripts/spoken_workflow.py init --source "$source" --transcript "$transcript" \
  --project-dir "$run/projects/chosen-name" --simulation-run "$run/run.json"
```

自行安排项目名，不询问普通用户 hash 或输出空目录。全文编辑、原声代理与 SRT 使用正常实现，不能另做旁路视频。`include_presenter` 默认 false：MG 可只用原声，避免无需求地编码一支人物中间片。若计划使用人物，先在稿件设置 true，再走同一次第一道确认。

没有真正音频输入时，在生成代理后如实记录：

```bash
python3 scripts/spoken_workflow.py record-capabilities --project-dir "$project" \
  --audio-input unavailable --reason '当前模型通道不接收音频；本轮仅测交互和技术链路，听感未测。'
```

只在已绑定的模拟 run 内生成 `mode=simulation` 的语义状态，听过秒数为 0。生产调用只写能力状态，不生成任何假的试听证据。后续 `manuscript-review`、`render-audio`、`director-review`、计划验证和初始化都走原工作流，仍要求两次独立模拟确认。对话只展示可读正文/方案和必要取舍，不把内部签名操作交给用户。

完成视觉创作后记录：

```json
{"status":"test-ready","needs_visual_production":false,
 "test_review":{"scope":"usability-only","hearing":"not-tested"}}
```

不填写假的 continuous 视听记录。测试导出：

```bash
node scripts/render_master.mjs --project-dir "$project/hyperframes" --plan "$plan" \
  --purpose simulation --output "$project/final/TEST-video.mp4"
node scripts/validate_master.mjs --plan "$plan" --final "$project/final/TEST-video.mp4" --output-dir "$project"
```

只有模拟 run 能用此 purpose；只能输出在同一 run 内且文件名为 TEST-*.mp4。初始化注入全程 `SIMULATED USER TEST · HEARING NOT TESTED` 水印，不能去掉。production/smoke 均拒绝模拟回执，生产 owner 身份不能签模拟请求，模拟控制器不能签生产请求。技术检查通过只说明链路可运行，绝不代表听感、内容或美术质量验收。
