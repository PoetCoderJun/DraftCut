# 完整口播流程迁移 / Full spoken-workflow migration

当前 DraftCut 从自然录音或一支口播视频开始：完整口播精剪 → **口播稿审核** → 正式精炼原声 → **视频脚本审核** → 视觉制作与成片。保留原声，用同一整数采样时间线生成音频与字幕；人物视频使用同剪辑顺序和累计帧分配。公开集成聚焦这条原声精剪与视觉制作流程。

## 原完整能力与补齐范围

MIT clean-talking-video 源提交 `598c95d` 的 Skill 包括：口头禅、口误、改口、失败重说、连续／跨句重复、停顿与首尾静音整理；只修正识别错误、术语、标点和断句；全文 Agent 判断、局部试听、用户完整字幕确认、统一音视频/SRT 映射。机械规则只标候选，不自动决定语义删除。本地工作版本另加第一次字幕确认前的精剪代理与语义复核；本集成将对应要求纳入审核包。

本次保留原项目 MIT 声明，导入保守候选生成与纯时间线／字幕助手，并在其上增加逐词完整记账、词级采样保护、可审查差异、移序映射、两次用户签名、内容变更失效和可重试事务。不复制无关私有业务、素材或凭据；原私有仓库可见性不变。

## Legacy 项目必须显式迁移

旧 `motiontalk.*.v1` 报告可以保留阅读；旧的 `approved=true`、`approval_text`、无人值守自批或气口批准不能继承到新生产流程。旧 `prepare_audio.py` CLI 拒绝直接作为正式音频入口。原项目与产物保留，不在原目录就地重写。

提供原始素材与逐词转写，导入新的空工作目录：

```bash
python3 scripts/spoken_workflow.py migrate --legacy-plan /path/old-plan.json \
  --source /path/original.wav --transcript /path/original-transcript.json \
  --project-dir /path/new-workflow-project
```

迁移记录旧计划路径与 hash，明确 `inherited_approvals=false`。重新完成全文编辑、语义复核、口播稿批准和视频脚本批准，再制作。没有原始素材／可信词级转写时停止，不能把旧成片或旧字幕当作已审核原稿静默过关。

## DraftCut compatibility

DraftCut 原名 MotionTalk；仓库为 [PoetCoderJun/DraftCut](https://github.com/PoetCoderJun/DraftCut)，新 Skill 名为 `draftcut`。中文默认 `README.md`，英文 `README_EN.md`，旧 `README.zh-CN.md` 保留切换入口。旧本地副本和 Skill 不自动改名或覆盖；确认后自行重新安装。

项目的生产契约升级到 `draftcut.workflow.v2`；旧 `motiontalk.*.v1` 质量报告名称保留兼容，不能作为新批准。内部 `.motiontalk-render.lock` 与 `MOTIONTALK_CHROME` 浏览器交接保留，以维持已有机器环境。依赖版本与根许可保持原设置；第三方代码继续遵循 MIT 等各自许可。

## Integration scope evidence

此前 `9f7fbdd` 音频集成只导入 ASR 和选中气口，其 [历史迁移说明](https://github.com/PoetCoderJun/DraftCut/blob/9f7fbddb09c588c43ac29944a851c5ac5f7bd9da/docs/audio-first-migration.md#L7-L9) 明确没有继承完整语义精剪。本次补齐这部分，不再把那份历史说明当作当前功能边界。

当前实现见 [spoken_edit.py](../scripts/spoken_edit.py)、[spoken_workflow.py](../scripts/spoken_workflow.py) 和 [签名审批](approvals.md)。源清单、逐词决定与审听证据进入第一道请求；正式原声与导演内容进入第二道请求。初始化、渲染和交付验证均检查当前签名链；所有例外都不能靠旧状态布尔值触发。
