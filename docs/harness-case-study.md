# DraftCut：从可审查提案到两次人工批准

[English](harness-case-study.en.md) · [使用方法](getting-started.md)

DraftCut 将语义判断交给 Agent 与人，将来源、时间线与批准完整性放到确定性代码中。正式流程是口播稿审核、视频脚本审核、成片。

## 口播编辑

[spoken_edit.py](../scripts/spoken_edit.py) 复用原 clean-talking 的保守候选和纯时间线助手，要求逐词完整记账。Agent 通读全文并听审，明确删除口头禅、口误／改口、失败重说、冗余重复、停顿的依据。否定、数字和名称有保守保护；敏感变更须写出具体理由供人审核。

每个保留词恰好进入输出一次，移序需说明。代码按整数采样拼接 48 kHz 原声，逐块比较输出 PCM 与源区间；所有保留词的完整采样范围都必须存在，删除词不能残留。字幕由保留词及同一映射生成，不能仅删字幕。词组断句和 ASR 字面纠错都在审核包中披露，不用 TTS 添加声音。

输入为视频时，同一采样区间决定视频片段；累计帧舍入将边界误差限制在帧精度，避免逐段舍入累积漂移。正式媒体完整解码。ASR 边界本身仍需听审，采样正确不能证明识别或自然度。

## 两次批准与失效

[spoken_workflow.py](../scripts/spoken_workflow.py) 先生成 REVIEW-ONLY 代理和完整差异稿，语义复核证据绑定稿件与代理。口播稿请求由用户签名后才可生成正式精炼音频。导演请求绑定正式音频、字幕、完整脚本、计划及素材，再次由用户签名。

[review_approval.py](../scripts/review_approval.py) 在用户本人终端审阅并确认当前摘要，用用户保管的加密 Ed25519 私钥签发回执。生产验证信任项目外公钥，不接受模型布尔值、自签测试身份、错误阶段或过期版本。内容变化在实际检查中被观察到时烧掉旧代次，即使恢复旧稿也需新的批准。失败构建保留在暂存事务目录，不当作已批准成品；同版本重试只返回已验证产物。

这依赖用户保管口令与主机信任配置，不能防御掌握整个执行环境和口令的攻击者。签名证明持钥者批准过具体内容，不证明审美、语义与听感。详情见 [审批边界](approvals.md)。

## 制作与交付

`validate_plan.py` 的纯函数只做结构检查；生产 CLI、初始化、导出和交付入口都重新校验两道签名链。`init_project.mjs` 按字节复制批准 WAV，生成的仍是 scaffold。Agent 必须实际创作 MG 并连续预览。

导出前后验证当前批准与工程音轨，导出后由 [verify_output_audio.py](../scripts/verify_output_audio.py) 比较解码波形和批准原声，检查音轨误换或时序不一致。mono→stereo 显式复制声道，避免隐式 downmix 造成虚假的增益差异。波形比较有 AAC 编码容差，不代替语义试听。

依赖继续锁定 Hyperframes 0.8.30、GSAP 3.14.2；默认单 worker、本机 Chrome、硬件 H.264，软件编码显式选择。技术元数据、实际听感和视觉判断分开报告。

## 可复查的本地验证

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s scripts/tests -v
node --test tests/*.test.mjs
python3 examples/plan-validation/run.py
python3 examples/full-workflow/run.py --output-dir /tmp/draftcut-full-example --initialize-composition
```

合成源为按词标记的音调、手写时间戳与独立 fixture 签名，不是实际 ASR 或真实人类批准。测试覆盖语义删改、敏感词和有意重复保留、移序、PCM完整性、SRT映射、人物音视频同剪辑、两道批准阻塞、变更失效、伪造与旧项目迁移。真实口播准确率、自然剪口、视觉质量和效率收益仍须用获授权录音与实际视听评估，未建立 100 倍基准。

## 从仓库链接安装的实跑范围

独立执行 Agent 从公开仓库链接读取 README → Agent bootstrap → SKILL，在 macOS Apple Silicon 的全新副本实际创建 `.venv` 并安装锁定 Node 包，随后重复检查并复用依赖。两次均执行了本机完整 Chrome + GSAP 与 H.264/AAC 编码、完整解码；再按健康报告的运行环境初始化合成工程，lint 为零错误零警告。

这证明当前机器上的隔离项目安装路径；已有系统 Python、Node、FFmpeg 和 Chrome 被复用，不代表在全新操作系统上安装全部系统软件，也不代表所有 Agent、云 ASR 或生产审批已认证。具体执行方法由 [Agent 安装说明](agent-bootstrap.md) 负责，用户仍只需发送仓库链接。
