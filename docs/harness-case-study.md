# DraftCut：可检查的 Agent Harness 工程案例

[English](harness-case-study.en.md) · [项目](../README.md)

音频到成片同时需要创意判断与机械约束。DraftCut 将它们拆开，让人能检查决定、产物与脚本各自承担什么。

| 阶段 | 可审查记录 | 机械边界 |
| --- | --- | --- |
| 意图 | 明确气口 yes/no、渐进创意 brief、可选素材/参考 | ASR 入口要求选择及单独云授权 flag |
| 音频 | 源 SHA-256、试听批准区间、采样保留/删除区间 | 拒绝错误源审核、词重叠和剪区重叠；字幕共用删除映射 |
| 规划 | 导演脚本与批准机器计划 | 正数画布/帧率/时长、已解决 brief、非空视觉 prompt、连续帧网格 cue |
| 初始化 | 音频优先可编辑工程、scaffold 状态 | 检查音频解码/时长与字幕边界；无需人物视频；不覆盖已有工程 |
| 制作 | 内容视觉与连续预览证据 | production 要求 ready 和存在的证据路径；合成 smoke 模式明确区分 |
| 交付 | 日志/渲染记录、技术报告、独立视觉/试听记录 | 尺寸/帧率、音频视频时长、H.264/AAC、单 MP4 目录 |

## 确定性与判断的边界

[prepare_audio.py](../scripts/prepare_audio.py) 只建议未分类词间间隙，不自动批准气口。Agent 必须试听选择，脚本才把批准气口默认保留到 0.25 秒。不剪则保留时间线。程序阻止词级时间戳重叠，但 ASR 时间不准仍可能暴露语音，不能证明节奏自然或音质合格。采样映射后 SRT 舍入到毫秒。

[validate_plan.py](../scripts/validate_plan.py) 检查结构与 cue 时间，不认证批准身份、不绑定批准版本、不检查媒体存在或视觉意义。[init_project.mjs](../scripts/init_project.mjs) 再检查音频解码、时长和字幕边界；生成的是 scaffold，不是完整创意成果。

[render_master.mjs](../scripts/render_master.mjs) 读取 Agent 记录的制作状态，确认预览证据路径存在；不解读证据像素，也不证明实际看过。固定依赖、单 worker 和可 seek 时间线便于检查，但不承诺不同硬件字节一致。硬件/软件编码明确选择。

[validate_master.mjs](../scripts/validate_master.mjs) 检查元数据及音轨时长，容差三帧；报告明确 scope=technical，视觉未被此程序评估。连续观看与实际试听是另外的真实审查任务。目前没有签名审批或整工程哈希绑定。

## 复现

```bash
python3 examples/plan-validation/run.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s scripts/tests -v
node --test tests/*.test.mjs
python3 examples/audio-only-smoke/run.py --output-dir /tmp/draftcut-fresh-smoke --render
```

最后一条命令用合成声音与作者编写时间戳，不调用云 ASR、不用私人录音。需要固定依赖、FFmpeg、本机 Chrome。只验证纯音频工程可渲染，不证明真实 ASR 准确率、自然气口判断、创意质量或耗时成本收益。见 [迁移说明](audio-first-migration.md)。

可迁移的思路是清楚的决定记录、窄的确定性门禁与独立评估的 Agent 判断，可用于 Work、Robotics、Finance 的探索；本媒体案例不代表企业部署、机器人能力、金融绩效或 ROI。

[非商业许可](../LICENSE.md) 未改，商业用途需事先书面授权；第三方材料保留自身权利。
