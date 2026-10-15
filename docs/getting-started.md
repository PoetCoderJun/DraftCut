# DraftCut 安装与使用 / Setup and usage

[中文首页](../README.md) · [English](../README_EN.md)

## Installation through your Agent

把 https://github.com/PoetCoderJun/DraftCut 发给 Agent，要求它安装配置、检查环境，然后进入口播制作。Agent 按 [安装与健康检查说明](agent-bootstrap.md) 探测本机、复用健康依赖、补齐缺失项并报告实际结果；本页不提供另一套用户安装入口。

<a id="environment"></a>
<a id="skill-installation"></a>

当前完整流程验证环境为 macOS，事务锁使用 POSIX `flock`。不声称所有 Agent／平台都已认证。旧 Skill 或项目保留，按 [显式迁移](audio-first-migration.md) 处理。

## Transcription configuration and consent

内置 DashScope 转写会上传音频且可能收费。配置 `DASHSCOPE_API_KEY`；也接受旧 `DASHSCOPE_ASR_API_KEY`。默认 base URL 是 `https://dashscope.aliyuncs.com`，`DASHSCOPE_ASR_BASE_URL` 优先于 `DASHSCOPE_BASE_URL`。默认模型在现有适配器中为 `qwen3-asr-flash-filetrans`，可配置 `DASHSCOPE_ASR_MODEL`。核对服务账号的区域、模型权限与价格，不静默切换供应商。

通过安全执行环境提供密钥，不放进提示词、日志或 Git；默认自动复用用户级私有配置，首次由安全输入提供一次；`--env-file` 只是可选覆盖，不需要每个项目重复设置。见 [API key 一次配置](configuration.md)。转写前须有明确上传／费用授权，已有持续授权覆盖当前录音时直接沿用，`--allow-cloud-asr` 本身不构成授权。云端上传压缩音频代理、异步识别并取回词级结果。已有可信逐词转写可本地导入。语义复核可沿用同模型审听代理识别，也可在审核包中明确披露完整人工试听方式，由用户批准；不会自动增加付费调用。

## Full spoken editing

逐词检查整份原稿，处理无意义口头禅、失败重说、改口、口误、冗余重复和停顿，保留否定、数字、专名、有意重复与论证结构。完整原稿、精炼稿、逐词差异和保留／删除依据一起交给用户。模型提出编辑方案；审核前的代理只用于听审，正式精炼原声必须等用户批准后生成。

[实际编辑字段与命令](../references/00-audio.md) · [用户审批设置](approvals.md)。源素材、稿件和证据按 hash 与修订代次绑定；变更令下游批准失效。输出逐采样拼接原声，不靠 TTS 添加内容。

## Video input

可以直接把一支口播视频作为 `spoken_workflow.py init --source` 的输入。程序保留原文件，抽取未剪辑原声作为规范化源；正式批准后按同一时间线剪原声与人物视频。音视频时间原点不同时显式停止，不能盲目拿未剪人物视频配剪后音轨。

素材文件夹和参考片仍可选。此流程聚焦现有录音或口播视频的精剪。

## What you review

1. **口播稿审核：**原稿／精炼稿、逐词保留删除依据、纠错、重排、停顿与全文听审证据。用户签名批准此版本后，才生成正式精炼音频与字幕。
2. **视频脚本审核：**在批准音频时间线上规划画面、MG、素材、重点与节奏。用户再次签名批准后，才初始化视觉工程、渲染与交付。

[两次批准的操作与信任边界](approvals.md)。Agent 自审、没有回复、旧批准和无人值守措辞不能代替其中任何一次。批准后连续完成当前版本，不反复索要“继续”。

## Delivery and validation

主交付是 MP4，可编辑工程与审核证据留在项目目录。每个正式精炼音频样本必须来自批准源区间；字幕和词级时间共用采样映射。人物视频使用累计帧边界防止多剪口累积漂移。导出后完整解码并对 AAC 解码波形与批准音频进行比较，防止字幕变化但声音未改、音轨被换或时序漂移。

技术验证不证明语义自然和审美正确。Agent 仍需连续预览与实际试听首、中、尾和所有剪口，分开记录判断；没有执行的标 pending。ASR 误识别和不准确词边界需先复核修订。

## Local verification

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s scripts/tests -v
node --test tests/*.test.mjs
python3 examples/plan-validation/run.py
python3 examples/full-workflow/run.py --output-dir /tmp/draftcut-full-example --initialize-composition
```

最后一个命令使用已知音调 PCM、手写词时间戳与独立临时测试签名，通过两道模拟审核并实际生成精炼音频、字幕与可初始化项目。它不伪装人类批准或实际 ASR／自然听感验收，也不会调用云模型。示例生产门只能处理这份已知合成输入，不能用 `example_only` 标签绕过真实项目审核。

## Examples and validation

首页的两个 GIF 来自作者既有成片，均为 6 倍速无声视觉展示：Vibe Working 原片 00:39–01:27，具身 AI 为原片最后 30 秒。它们不是新流程的端到端验收。

Opus 5.5、ChatGPT 6 Astra、Kimi k3 是作者推荐，Agent 实际能力取决于本地文件、命令、视觉与试听工具；没有逐一认证所有平台。首页的 100 倍是减少人工剪辑投入的愿景，尚无对照基准或普遍实测保证。

SVG 为原创可编辑示意，不是实际产品界面、音频实测或客户结果。测试与真实生产结果分别记录；技术、听感与视觉结论各有适用范围。
