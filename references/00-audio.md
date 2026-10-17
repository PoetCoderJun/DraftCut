# 完整口播精剪与第一道审核

所有路径由 Agent 管理，原素材不覆盖。录音与一支口播视频均可输入；多源录屏对齐不在本流程内。

以下完整文稿复核适用于干净成片；用户在对话中明确批准当前版本后自动出片，不要求终端签名。旧签名包装路径另见审批文档；试听可选，未试听不阻止输出审核包。用户明确授权且带独立 run 清单的模拟交互测试，按[测试说明](../docs/simulation-testing.md)记录能力限制与两次模拟确认；不能把测试标成真实听审或生产批准。

## 1. 转写和导入

内置 ASR 来自 clean-talking-video。使用前确认已有明确云上传／费用授权覆盖当前素材、有效期与预算；有效持续授权直接沿用，不为每个视频重问。没有或超范围时才取得授权，不能把 key 存在或工程改造授权当作付费服务授权。

```bash
python3 <skill-root>/scripts/transcribe_audio.py --audio "$source" \
  --output-dir "$work/asr" --allow-cloud-asr
python3 <skill-root>/scripts/spoken_workflow.py init --source "$source" \
  --transcript "$work/asr/transcript.json" --project-dir "$work/project"
```

已有逐词转写可直接导入，不新增云调用；核对其完整性与词边界。导入生成未剪辑的 48 kHz/24-bit 原声副本、源哈希、完整词表及 `manuscript.json`。这不是精炼音频。视频的音视频时间原点不同时显式停止并先处理对齐。

## 2. 全文内容精剪

逐段读完全部词，结合完整上下文决定保留／删除：无意义口头禅、口误、改口、失败重说、冗余重复与停顿。连续／跨句失败重说通常保留最后一次完整自然表达；相似但承担不同论证作用的句子、有意重复、否定、数字和专名不能机械删除。

机械 `candidate_review_items` 来自原项目，只提候选。`suggested_pause_keep_segments` 只是停顿建议，不自动执行。修改 `manuscript.json`：

- `decisions`：每个词恰好一项 `id/action/category/reason`。`action` 为 keep/delete；分类为 retain/filler/mistake/correction/retake/redundant_repeat/pause。
- `order`：全部保留词的 ID，恰好一次；移序要写 `reorder_reason`，完整披露给用户。
- `reviewed_word_ids`：通读并复核过的全部原词，不能只填候选。
- `protected_terms`：补充本项目专名。否定、数字、显著英文名称另有保守保护；若改口确需删除其中一项，要逐词写具体 `sensitive_change_reason`，由用户看到并批准。
- `corrections`：按原词 ID 修正 ASR 字面错误，提供 `text/reason/evidence`（逐词ASR、源草稿、用户明确确认或可选试听的实际依据；兼容旧 `listening_evidence`）；敏感词变动另需敏感变更理由。只纠正实际原声，不能加原声没有的词、靠改字幕伪装音频已剪，也不调用 TTS 补词。
- `pause_deletions`：原时间线的 `start/end/reason`，只能在词外间隙。保留有意义停顿，剪点不得截断词级区间，以样本映射检查验证。
- `caption_groups`：可选，按输出次序分组原词 ID，用于断句；不能漏词、复制词或新增文本。
- `include_presenter`：视频输入的默认干净成片阶段设 true，人物与原声共用同一剪辑时间线；纯音频输入或用户明确仅要文稿时不无需求地编码人物中间片。

每次内容变化递增 `revision`，更新全文复核和时间线证据。所有审核还会绑定实际内容摘要和系统修订代次；只改 revision、状态或布尔字段不能获得批准。

## 3. 可选审听代理与全文文字复核

```bash
python3 <skill-root>/scripts/spoken_workflow.py preview --project-dir "$work/project"
```

生成 `previews/.../REVIEW-ONLY.wav` 与 `preview.json`；该代理仅供审核，未批准不能作为正式精炼音频或进入导演制作。

默认通读原片逐词转写与候选口播全文，逐项核对保留／删除、否定、数字、专名、改口与字幕边界。冲突可结合用户草稿和明确的词语确认裁决，不要求用户试听。已有同模型代理ASR时辅助对照；需要新增上传／费用时仍按授权范围执行，不为输出审核稿自动增加调用。

记录 `semantic-review.json`：

```json
{
  "mode": "text-review",
  "manuscript_digest": "从 preview.json 读取",
  "preview_sha256": "从 preview.json 读取 audio_sha256",
  "reviewed_word_ids": ["全部原词 ID"],
  "hearing": "not-tested",
  "source_listened_seconds": 0,
  "preview_listened_seconds": 0,
  "findings": "全文删改、逐词映射检查结果，已确认纠错与未解决的疑点",
  "review_disclosure": "本次按完整文稿及逐词时间线审核，未试听；试听不是批准前提"
}
```

未试听时如实保留零时长，不能填成全片时长。`same-model-asr` 模式另填 `asr_transcript/asr_sha256/source_model/review_model`，转录的 source 必须指向该代理；不试听时同样填 `hearing=not-tested`、零时长及 `review_disclosure`。源稿、用户确认是纠错依据，不授权添加原声没有的内容或编造词时间戳。确实做了全段试听时可保留旧 `human-listening` 模式并记录实际范围，此路径完全可选。任何稿件或源素材变化后代理与文稿复核证据都需更新；PCM未变化的本地文字修订可复用已有ASR并记录其对应关系，不自动新增云调用。

## 4. 口播稿审核

```bash
python3 <skill-root>/scripts/spoken_workflow.py manuscript-review --project-dir "$work/project"
```

脚本生成的 `review.md` 与 `subtitle-review.srt` 是内部审核证据，Agent 读取后必须把完整精炼口播稿、简短删改依据和未解决疑点直接输出在当前命令行／Codex 对话正文；不要只返回路径或链接，不要求用户打开文件，不为展示额外另存一份文稿。原稿、逐词差异、纠错、移序、停顿及复核方式保留在内部审核包中，用户要求时再直接展开。仅在用户明确要求只交文稿、不制作时停止；普通视频任务在用户明确批准当前文稿后，自动按[干净成片](04-clean-cut.md)交付视频，不要求再发渲染指令、试听或终端签名。下面的 `render-audio` 仍是旧签名包装路径的入口，不能拿它的门禁阻止独立干净出片。

## 5. 干净成片与旧签名包装路径

默认按[干净成片](04-clean-cut.md)生成正式原声、人物精剪和旁挂字幕。以下命令仅用于保留的旧签名包装工具链：

```bash
python3 <skill-root>/scripts/spoken_workflow.py render-audio --project-dir "$work/project"
```

先检查素材、转写、稿件、代理、语义证据、审核包、修订代次及用户签名。正式音频逐采样拼接原声，不变速、不重新合成；字幕和每个保留词共用整数采样映射。若输入带人物视频，使用同一剪辑顺序和累计帧边界生成同步视频。可重试同一个已批准版本，但不能改写已生成的产物。

输出版本目录中的 `narration.wav/final.srt/transcript.json` 是下一阶段唯一音频与字幕依据。旧的 `prepare_audio.py` CLI 不再构成生产入口；旧项目必须显式迁移并重新审核。
