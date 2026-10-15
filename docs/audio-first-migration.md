# Audio-first migration / 音频优先迁移

DraftCut now accepts a user audio file with optional materials. ASR, the explicit breath choice and aligned subtitles are managed inside the workflow. Existing prepared-video/SRT requests should be discussed as existing assets, not required from every user; extract/use their approved audio only if authorized and keep the supplied originals.

This branch incorporates the author's local Hyperframes upgrade (base `c14660f`) and reviewed working changes, replacing the public Remotion renderer. It retains the optional source-based mastering script without enabling mastering by default. Runtime dependencies are pinned. Render defaults remain one worker/local Chrome/hardware H.264, with explicit software smoke/production options.

New preparation edits **only reviewed breath gaps**, retaining 0.25 seconds by default. It does not inherit clean-talking-video's broader filler/retake editing scope. A no-trim choice preserves the timeline. Internal SRT is remapped against the same sample deletions as the prepared audio.

The original clean-talking-video repository remains the independent raw-video cleanup workflow. Its CLI and files are unchanged by the audio integration. Minutes continues using its existing clean-talking-video ASR dependency; DraftCut is not a replacement backend for Minutes. Nothing is archived or deleted.

根许可证不变；第三方 ASR 模块保留 MIT 许可，其他依赖适用自身条款。音频、本地成片和参考素材不会自动上传或公开。旧 Remotion 契约测试不再适用于新引擎，替换为音频剪辑/字幕、纯音频初始化、渲染参数和元数据测试；旧测试及原公开树已在任务审查快照中保留。

## DraftCut compatibility

DraftCut is the current project name; MotionTalk is the former name. The canonical repository is [PoetCoderJun/DraftCut](https://github.com/PoetCoderJun/DraftCut), and the new Skill identifier is `draftcut`. `README.md` is now Chinese; `README_EN.md` is English. `README.zh-CN.md` remains a link to the Chinese homepage for older bookmarks.

Existing local clones and installed Skills are not renamed or overwritten. In a clone you own, update its remote when convenient with `git remote set-url origin https://github.com/PoetCoderJun/DraftCut.git`; this does not update local files or the installed Skill. Reinstall deliberately before using `$draftcut`. An old `$motiontalk` invocation continues to refer to the version your Agent already has installed; it is not an alias automatically registered by this repository.

The rebrand preserves `motiontalk.audio-preparation.v1`, `motiontalk.quality-report.v1`, `.motiontalk-render.lock` and the internal `MOTIONTALK_CHROME` handoff so existing reports, concurrent-render protection and browser launching keep their contracts. A legacy Python module name in the validation example is also harmless and retained. CLI arguments, output names, dependency versions and approval behavior are unchanged. The private npm runtime package is renamed to `draftcut-hyperframes-runtime`; it is not published to npm.

This integration imported ASR and selective breath-gap preparation. It did not import the broader semantic cleanup workflow or its full-subtitle approval gate. The current human creative approval is the video director script and plan; audio preparation is not a second mandatory manuscript-approval stage. See [the review table](getting-started.md#what-you-review).

## Integration scope evidence

The limited scope predates the DraftCut rename. The original integration commit [9f7fbdd](https://github.com/PoetCoderJun/DraftCut/commit/9f7fbddb09c588c43ac29944a851c5ac5f7bd9da) explicitly states in its [migration note](https://github.com/PoetCoderJun/DraftCut/blob/9f7fbddb09c588c43ac29944a851c5ac5f7bd9da/docs/audio-first-migration.md#L7-L9) that preparation edits reviewed breath gaps and does not inherit broader filler/retake editing. The commit records that scope, but does not explain a broader product rationale for choosing it.

The public implementation matches that decision:

- The imported vendor directory contains the ASR adapter, its package marker and license. [transcribe_audio.py](../scripts/transcribe_audio.py#L24) invokes only that transcription adapter, not a semantic video-editing workflow.
- [prepare_audio.py](../scripts/prepare_audio.py#L54) proposes gaps **between word timestamps**, initially unclassified and unapproved. Its `selected_deletions` function accepts only approved `kind=breath` intervals with a listening reason, and rejects intervals overlapping speech. It does not select spoken phrases or retakes for removal.
- The preparation review binds selected gaps to an audio hash; it is not a whole-transcript user approval. [validate_plan.py](../scripts/validate_plan.py#L29) checks the director plan's approval and the explicit breath choice, but has no separate manuscript/subtitle-review approval state.
- [Planning](../references/01-plan.md) proceeds from prepared audio and aligned subtitles to the director script and machine plan. [The Skill](../SKILL.md) routes approval of that plan into production and delivery; no intervening spoken-manuscript approval stage is defined.

因此，可以确认当时合入的是转写与气口准备，完整语义精剪及其独立审核流程并未接入；不能把“合入 clean-talking”解读为全部能力迁移。这里仅记录已有实现，没有新增流程或改变审核规则。
