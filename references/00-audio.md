# 完整口播精剪与第一道审核

所有路径由 Agent 管理，原素材不覆盖。录音与一支口播视频均可输入；多源录屏对齐不在本流程内。

以下完整听审与 owner 签名要求适用于生产。用户明确授权且带独立 run 清单的模拟交互测试，按[测试说明](../docs/simulation-testing.md)记录能力限制与两次模拟确认；不能把测试标成真实听审或生产批准。

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

逐段读完全部词，结合实际试听决定保留／删除：无意义口头禅、口误、改口、失败重说、冗余重复与停顿。连续／跨句失败重说通常保留最后一次完整自然表达；相似但承担不同论证作用的句子、有意重复、否定、数字和专名不能机械删除。

机械 `candidate_review_items` 来自原项目，只提候选。`suggested_pause_keep_segments` 只是停顿建议，不自动执行。修改 `manuscript.json`：

- `decisions`：每个词恰好一项 `id/action/category/reason`。`action` 为 keep/delete；分类为 retain/filler/mistake/correction/retake/redundant_repeat/pause。
- `order`：全部保留词的 ID，恰好一次；移序要写 `reorder_reason`，完整披露给用户。
- `reviewed_word_ids`：通读并复核过的全部原词，不能只填候选。
- `protected_terms`：补充本项目专名。否定、数字、显著英文名称另有保守保护；若改口确需删除其中一项，要逐词写具体 `sensitive_change_reason`，由用户看到并批准。
- `corrections`：按原词 ID 修正 ASR 字面错误，提供 `text/reason/listening_evidence`；敏感词变动另需敏感变更理由。只纠正实际原声，不能加原声没有的词、靠改字幕伪装音频已剪，也不调用 TTS 补词。
- `pause_deletions`：原时间线的 `start/end/reason`，只能在词外间隙。保留有意义停顿，剪点听审不吞字。
- `caption_groups`：可选，按输出次序分组原词 ID，用于断句；不能漏词、复制词或新增文本。
- `include_presenter`：默认 false，只用原声制作 MG；计划使用人物画面时在本次审核前设 true，按同一剪辑时间线生成，不无需求地编码人物中间片。

每次内容变化递增 `revision`，再次试听。所有审核还会绑定实际内容摘要和系统修订代次；只改 revision、状态或布尔字段不能获得批准。

## 3. 审听代理与语义复核

```bash
python3 <skill-root>/scripts/spoken_workflow.py preview --project-dir "$work/project"
```

生成 `previews/.../REVIEW-ONLY.wav` 与 `preview.json`；该代理仅供审核，未批准不能作为正式精炼音频或进入导演制作。

优先沿用同一模型转写这个代理，逐段比较预期字幕，原转写与代理转写冲突时实际试听裁决。需要再次上传时仍按已有授权范围执行，不自动增加付费请求。无云调用时可用完整人工试听替代，但必须在审核包披露该方式，由用户签名确认。

记录 `semantic-review.json`：

```json
{
  "mode": "human-listening",
  "manuscript_digest": "从 preview.json 读取",
  "preview_sha256": "从 preview.json 读取 audio_sha256",
  "reviewed_word_ids": ["全部原词 ID"],
  "source_listened_seconds": 0,
  "preview_listened_seconds": 0,
  "findings": "实际全文和剪口听审结果，问题与修订",
  "offline_review_disclosure": "本次采用完整试听，未进行云端二次 ASR"
}
```

时长填实际完整复核范围；不能复制示例 0 或伪称试听。`same-model-asr` 模式另填 `asr_transcript/asr_sha256/source_model/review_model`，转录的 source 必须指向该代理。任何稿件或源素材变化后代理与证据都需更新。

## 4. 口播稿审核

```bash
python3 <skill-root>/scripts/spoken_workflow.py manuscript-review --project-dir "$work/project"
```

向用户交付返回的完整 `review.md` 与 `subtitle-review.srt`：原稿、精炼稿、逐词差异、删除／保留依据、纠错、移序、停顿及审听方式都在其中。**停下等待用户批准**。用户在自己的终端按 [审批设置](../docs/approvals.md) 审阅并签发当前 `request.json` 的回执；Agent 不能代签。

## 5. 批准后生成正式原声

```bash
python3 <skill-root>/scripts/spoken_workflow.py render-audio --project-dir "$work/project"
```

先检查素材、转写、稿件、代理、语义证据、审核包、修订代次及用户签名。正式音频逐采样拼接原声，不变速、不重新合成；字幕和每个保留词共用整数采样映射。若输入带人物视频，使用同一剪辑顺序和累计帧边界生成同步视频。可重试同一个已批准版本，但不能改写已生成的产物。

输出版本目录中的 `narration.wav/final.srt/transcript.json` 是下一阶段唯一音频与字幕依据。旧的 `prepare_audio.py` CLI 不再构成生产入口；旧项目必须显式迁移并重新审核。
