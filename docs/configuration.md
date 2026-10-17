# API key 一次配置，后续自动复用

这是给安装 Agent 的说明。用户仍从 README 的仓库链接开始；不用为每个视频创建 `.env` 或重复提供 key。默认只用一个用户级文件，位于 checkout 与视频工程之外，重装／升级仓库不会覆盖它。

## 第一次与之后

1. Agent 先执行 `python3 <skill-root>/scripts/configure_asr.py status`（或读取 bootstrap 的 `capabilities.asr`），只获取状态与配置路径，不读取密钥正文到模型上下文。
2. 已有有效格式的用户配置或平台安全注入变量时直接复用，不再问 key。`configured_not_verified` 表示尚未联网验证账号，不能因此要求重新配置一次。
3. 只有确实缺配置时，优先复用 Agent 平台已有的安全密钥注入；否则请用户在自己的本地终端运行一次 `python3 <skill-root>/scripts/configure_asr.py setup`。Agent 应给出实际安装路径，不让用户猜目录。工具用隐藏输入接收 key，私有保存；不要让用户把 key 发到聊天、作为命令参数，或由模型代输。
4. 以后用户只给录音与风格要求。脚本从同一用户配置自动读取，不需要 `--env-file`。失效密钥、权限或格式错误给出一次有针对性的修复动作；网络失败不等于要再次索取 key。用户明确要求更换配置时才使用 setup 的 `--replace`；指定账号区域／模型可用 `--base-url`／`--model`。

本轮开发不替真实用户执行 setup、不读取或迁移现有真实 key，也不创建新的账号访问。实际首次保存凭据由用户本人明确执行。

## 固定路径与优先级

| 系统 | 默认用户配置 |
| --- | --- |
| macOS | `~/Library/Application Support/DraftCut/asr.env` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/draftcut/asr.env` |
| Windows | `%APPDATA%/DraftCut/asr.env`（仅路径选择测试，完整制作仍受 POSIX 平台限制） |

选择规则明确且不扫描项目：进程环境变量优先；文件来源按显式 `--env-file`、环境变量 `DRAFTCUT_ASR_CONFIG`、默认用户文件三者顺序选一个。override 文件替代默认文件，不混合两个文件；`DRAFTCUT_ASR_CONFIG` 必须是绝对路径。进程中的密钥或 base URL 会覆盖文件中的对应两种别名，避免旧 ASR 专用名反压新进程配置。

不会搜索 CWD、checkout、父目录或随意的 HOME `.env`；切换项目不会改变默认配置来源。可选 override 用于临时账号或特殊执行环境，普通用户不需要每次传参。

setup 新建用户目录权限为 700、文件为 600；POSIX 加载前检查 owner 与私有权限。已有配置默认原样保留，安装／健康检查只读，显式 `--replace` 才原子替换。权限不正确时按状态提示在自己的终端修复选定文件（例如 chmod 600），不要打印内容。Windows 文件 ACL 尚未认证，当前完整流程不支持 Windows。

## 安全状态与可选字段

`configure_asr.py status` 和 `transcribe_audio.py --check-config` 都不联网、不鉴权、不上传、不产生费用、不输出密钥或服务 URL。`needs_configuration` 是缺 key；`invalid_configuration` 给出不含原值的格式／权限错误；`configured_not_verified` 是配置可读取且格式有效，账号、额度及模型权限仍由真实调用验证。

安装 Agent 只需要调用状态或加载脚本。不要用 cat、读取文件工具、打印环境变量或调试日志，把私有文件正文带入模型上下文。不要为诊断索取密钥正文。

高级用户可参考 [`.env.example`](../.env.example)。文件支持 UTF-8 的字面 `KEY=VALUE`、可选 export、单／双引号和注释，不执行 shell，不展开变量。只读取以下 ASR 设置，其他文件变量不传入子进程：

| 变量 | 默认值／含义 |
| --- | --- |
| `DASHSCOPE_API_KEY` | 内置云 ASR 凭据；兼容旧 `DASHSCOPE_ASR_API_KEY`；同一来源内旧 ASR 专用名优先 |
| `DASHSCOPE_ASR_BASE_URL` | 默认 `https://dashscope.aliyuncs.com`；兼容 `DASHSCOPE_BASE_URL`，按账号区域设置 HTTPS 服务 |
| `DASHSCOPE_ASR_MODEL` | 默认 `qwen3-asr-flash-filetrans`，需提供逐词时间戳 |
| `DASHSCOPE_ASR_POLL_SECONDS` | 默认 2，最少 0.5 秒；有限正数 |
| `DASHSCOPE_ASR_TIMEOUT_SECONDS` | 默认 3600，最少 30 秒；有限正数 |

Agent 自己的模型登录或 OpenAI key 不能替代 DashScope key。只有内置云转写需要它；安装、本地精剪／渲染、导入可信完整逐词转写无需 DraftCut API key。图形与 GSAP 在本地制作，不需要额外素材服务凭据；没有外部 HyperFrames Skill 时用本仓库 references 和锁定 CLI 的帮助。

## key 与上传／费用授权分别处理

保存 key 不构成上传或费用授权。首次确有云转写需求时，说明发送的内容、供应商、可能费用，并按用户选择记录仅本素材或指定目录／项目范围、有效期和预算的持续授权。保留用户原话与来源、范围，已有明确授权覆盖当前素材时直接沿用，不为每个视频重问；超范围或授权不清时才补问。`--allow-cloud-asr` 只是内部执行参数，不是授权证据。本轮没有签发或保存任何真实授权。

## 其他能力边界

当前实际验证 macOS Apple Silicon，Linux 运行与 CJK 字体仍需本机检查；Windows 制作流程明确 blocked。沿用 bootstrap 给出的 Python、PATH 和 `DRAFTCUT_CHROME`；不要硬编码作者路径。中文需实际截图核对，技术检查不证明全文听审或连续观看。

API 配置与内容审核互不替代。干净成片按真实对话中的当前文稿批准自动交付，无需终端签名。旧签名包装路径保留，独立可验证的宿主签发接口缺口见[对话批准边界](conversational-approvals.md)。签名口令不应存入 ASR 文件，临时 HOME 也不能重定向生产信任锚。
