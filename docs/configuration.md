# 配置与首次使用能力 / First-run configuration

给 Agent 的配置说明；用户仍从 README 的仓库链接入口开始。配置在实际安装路径运行，不依赖作者电脑上的密钥、转写缓存或私有 Skill。

## 哪些配置必需

| 工作 | 需要什么 | 不代表什么 |
| --- | --- | --- |
| 安装、本地精剪、图解、渲染 | bootstrap 通过的 Python/Node/FFmpeg/完整 Chrome | 不需要 DraftCut API key；不证明视听能力 |
| 导入已有转写 | 与源文件核对过的完整逐词时间戳 | 不需要云密钥；普通无词时间 SRT 不能直接替代 |
| 内置云转写 | DashScope 凭据、正确区域/模型权限、当前素材的上传/费用授权 | Agent 自己的模型登录或 OpenAI key 不能替代 DashScope key |
| 两道生产批准 | 当前后备实现需要本人签名；目标对话适配器尚未接入，见[明确缺口](conversational-approvals.md) | Agent 自填聊天记录、环境变量、fixture 身份不能代签 |
| 完整听审/连续预览 | 当前 Agent 通道实际具备音频输入/连续观看能力，或如实披露的人工试听路径 | 播放器、截图、ASR 成功不等于 Agent 已听过/看完 |

内置只有 DashScope 适配器，不会自动切换到 Whisper、OpenAI、Agent 登录或其他供应商。已有合法可靠的词级转写可按 [口播精剪](../references/00-audio.md) 导入，不新增云调用。图形和 GSAP 在本地制作；需要额外模型生成素材时另行核对该工具的能力、权限与费用，默认渲染不需要素材服务的凭据。没有外部 HyperFrames Skill 时直接按本仓库 references 与锁定 CLI 的 `--help` 制作，不让用户再安装一组未声明的私有 Skill。

## `.env` 只显式读取

默认只读取当前进程环境，不自动寻找或执行 `.env`。Agent 可通过平台安全配置注入凭据，或在用户选定的私有文件中配置；不要让用户把密钥发到聊天。 安装 Agent 只接收配置文件路径并调用加载脚本；不要用 cat、读取文件工具、打印环境变量或调试日志把私有文件正文带入模型上下文。需要排错时只查看 `--check-config` 的无密钥状态与错误，不能为诊断而索取密钥正文。

显式文件用法（由 Agent 执行）：

```bash
python3 scripts/bootstrap.py --env-file /absolute/path/to/private.env
python3 scripts/transcribe_audio.py --check-config --env-file /absolute/path/to/private.env
```

实际转写时对同一入口带上 `--env-file`，以及已有的素材、输出目录和授权参数。安装时选择文件不会把它永久存进工程，后续转写仍须明确选择。`--check-config` 不要求录音或上传许可，不联网、不创建转写目录；退出 0 只表示配置存在且格式有效，不表示账号、余额、模型或网络已验证。

可参考仓库 [`.env.example`](../.env.example)。文件仅支持 UTF-8 的 `KEY=VALUE`（可加 `export`）、单/双引号和行尾注释；不执行 shell，不展开 `$VAR`、`$(...)` 或反引号。只读取下表的 ASR 变量，文件中的其他变量不传入子进程；进程中的同名配置优先，有进程凭据时文件中的两种密钥名都不会覆盖它。`.env`/`.env.*` 被 Git 忽略；真实文件应由用户安全保存并限制访问权限。

| 变量 | 默认值/含义 |
| --- | --- |
| `DASHSCOPE_API_KEY` | 使用内置云 ASR 时必需；也支持旧 `DASHSCOPE_ASR_API_KEY`，同时存在时旧的 ASR 专用名优先 |
| `DASHSCOPE_ASR_BASE_URL` | 默认 `https://dashscope.aliyuncs.com`；优先于 `DASHSCOPE_BASE_URL`；按账号区域明确选择 HTTPS 服务，不静默换区 |
| `DASHSCOPE_ASR_MODEL` | 默认 `qwen3-asr-flash-filetrans`；需支持逐词时间戳 |
| `DASHSCOPE_ASR_POLL_SECONDS` | 默认 2 秒，最少 0.5 秒；有限正数 |
| `DASHSCOPE_ASR_TIMEOUT_SECONDS` | 默认 3600 秒，最少 30 秒；有限正数 |

健康报告只返回配置状态，不输出密钥或配置 URL。签名口令不能放进 `.env`。生产信任锚固定在操作系统账号的 `~/.config/draftcut/`；临时 `HOME`/`XDG_CONFIG_HOME` 不能重定向它。干净安装测试不应调用生产 setup，也不能用临时 HOME 声称已隔离生产身份；审批缺失路径应用 fixture 验证，测试身份使用独立 simulation/fixture 协议。

## 平台与浏览器

目前实际验证 macOS Apple Silicon；Linux 的工具路径及 CJK 字体、其他 Agent 的视听能力仍需本机验证。Windows 会明确阻止当前 POSIX 流程。Chrome 支持标准位置、用户 Applications、PATH 中的 Google Chrome，以及显式 `--browser-executable` 或 `DRAFTCUT_CHROME`。Agent 沿用 bootstrap 的 `runtime.path_prefix` 与 `runtime.environment`；不借用作者的 fnm 路径或 Python venv。

GSAP 随工程复制，本地默认无需远程字体/媒体；中文在目标机器实际截图核对，缺 CJK 字体时由 Agent 使用许可允许的本地字体并验证。系统软件缺失/权限不足、网络安装失败、无音频输入、未配置签名都要明确报告，不能用缓存、截图或合成测试替代真实可用性结论。
