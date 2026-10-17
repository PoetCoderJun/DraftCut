# Agent 安装与健康检查 / Agent bootstrap

**给执行 Agent 阅读。** 用户的唯一安装入口是把 https://github.com/PoetCoderJun/DraftCut 发给 Agent，要求安装配置并制作口播视频。不要让用户逐条执行下面的技术命令，也不要改成多个安装选项。安装结束后继续读取 [SKILL.md](../SKILL.md)；两次内容审核仍由用户完成。

## 1. 找到安全的工作副本

先读仓库 README、此文档和 SKILL。检查当前目录、已有安装、Git remote、分支与工作区。复用属于用户且版本合适的现有安装；有未提交改动或并行任务时，使用新的隔离副本，不能 reset、覆盖旧 Skill 或污染用户视频工程。不要仅凭目录名字判断仓库。

需要新副本时，由 Agent 在选定的空路径执行：

```bash
git clone https://github.com/PoetCoderJun/DraftCut.git /chosen/empty/path/DraftCut
cd /chosen/empty/path/DraftCut
```

记住实际安装路径；随后直接读取该路径的 `SKILL.md`。不要求用户理解安装目录、手工配置 Skill 发现机制或先运行另一个安装器。Agent 平台有自己的技能注册机制时，遵循该平台已知约定，并保留可直接读取 SKILL 的路径，不编造所有平台都已测试。

## 2. 探测已有环境，补齐缺失项

当前工作流使用 macOS/Linux POSIX、Python 3.10+、Node.js 22+、FFmpeg/ffprobe 和本机完整 Google Chrome。已实际验证 macOS，未认证所有操作系统／Agent。Apple Silicon 需要原生 ARM64 Node/Chrome。Hyperframes **0.8.30** 与 GSAP **3.14.2** 按锁文件安装；不升级，不自动下载 managed/headless-shell 浏览器。

Agent 先用本机可用工具确认 Python/Node/FFmpeg/Chrome 的位置和版本，复用健康依赖。缺少系统组件时，沿用机器已有的可信软件管理方式安装或选择已有的正确版本；只对确实需要的系统权限／管理员操作请用户接手。不要自动安装新的系统包管理器、运行来源不明的下载脚本、换平台或让用户手工拼凑依赖。没有可用安装权限时准确报告缺少的组件与失败动作，继续完成不受影响的工作。

由 Agent 运行：

```bash
python3 scripts/bootstrap.py --install
```

脚本使用项目 `.venv`，复用通过版本与依赖检查的 Python/Node 包；缺失或不符时执行项目内 `venv`、`pip install -r requirements.txt` 和锁定的 `npm ci`。不写全局 Python，不删除旧环境；已有不完整或伪装的 `.venv` 必须保留并改用安全副本。系统组件缺失会明确 blocked，交回 Agent 处理后重试。

`--browser-executable /absolute/path/to/GoogleChrome` 只选择已经安装的完整 Chrome。脚本不会下载浏览器、创建审批身份、输出密钥或调用转写服务。安装命令可能访问 Python/npm 软件仓库，需要按执行环境的正常网络授权路径操作；不能把网络失败写成安装完成。

ASR 配置是可选能力，不是安装前提。`capabilities.asr` 安全报告缺配置、配置无效或配置存在，不会登录、上传或验证余额。默认自动复用固定用户级配置；已有配置不再索取 key。确实缺少且用户需要云转写时，只引导一次平台安全注入或本地 `configure_asr.py setup` 隐藏输入，之后跨项目复用；安装不会写入或覆盖凭据。`--env-file` 仅为可选 override，不是每次制作的步骤。见 [API key 一次配置](configuration.md)。

## 3. 检查能否实际工作

安装后的脚本会检查包版本／依赖、运行锁定 CLI、在临时目录实际编码并完整解码 H.264/AAC，并用锁定渲染器相同的 CDP 自动化路径让本机完整 Chrome 加载本地 GSAP、执行变换并正常关闭。只绑定临时用户目录，不复用用户浏览器配置，不降低浏览器沙箱保护；检查结束清理自己的临时文件。环境限制阻止 Chrome 启动时，按正常工具授权路径处理，不能绕过安全设置或静默跳过检查。

再次执行只检查、复用依赖的路径：

```bash
python3 scripts/bootstrap.py
```

读取 JSON 的 `status/actions/checks/blockers/runtime/capabilities`，不能只看命令启动。`ready` 只说明本机依赖与基础媒体检查通过，不代表云 ASR 可用、人类审批已配置、真实声音自然或视频创作已经完成。失败为非零退出和 blocked。执行后向用户简要报告实际安装位置、复用／安装了什么、通过的检查与尚需授权的步骤。

后续命令使用报告中的 Python，并让 Node 调用 Python 子进程时沿用同一环境，例如由 Agent 设置：

```bash
export PATH="/actual/DraftCut/.venv/bin:/actual/native-node/bin:$PATH"
```

上面的路径必须换成健康报告给出的真实路径。不要把这个配置任务转交给用户。同时沿用 `runtime.environment` 的 `DRAFTCUT_CHROME`，使自定义 Chrome 路径在 check/snapshot/导出时保持一致。

## 4. 进入口播制作

环境就绪后按 [SKILL](../SKILL.md) 接收真实录音与效果要求。已有可信逐词转写可以本地导入。内置 ASR 使用 DashScope，需要针对素材的上传／费用授权；环境通过不等于获得这项授权。先复用已配置状态；确实缺少时才引导一次安全输入，不在聊天中要求粘贴密钥，不写入 Git 或日志，也不替用户开通付费账户。用户文件由脚本自动加载，不读取或打印配置正文到模型上下文。已有明确上传／费用授权覆盖当前素材时沿用，超范围才补问；key 存在本身不构成授权。

没有素材和云授权时可运行 [完整合成 fixture](../examples/full-workflow/README.md) 作为本地流程证明。它不证明真实 ASR 或人类审批。真实素材先在当前对话审核完整口播稿；明确获批后自动按[干净成片](../references/04-clean-cut.md)出片，不要求终端签名或额外继续指令。包装另行审核导演脚本。旧签名包装工具链的身份与口令按[审批说明](approvals.md)由本人保管，Agent不代创建或代签。

先按 [配置与能力边界](configuration.md) 检查当前通道的实际视听能力，并一次说明缺项。`capabilities` 中 owner 签名与 Agent 视听能力默认 `not_checked`，不能从依赖通过推断它们已就绪。真实直接用户对当前完整文稿的明确批准可触发独立干净出片；无音频感知能力或未配置签名不阻止该阶段。旧签名包装入口仍须本人设置与签发回执；对话确认不自动产生加密签名，不宣称已具备可信宿主签发器。

干净成片已使用真实对话中的文稿确认；仍保留的签名包装后备路径有额外用户操作，属于该路径的使用缺口。见[对话批准接入边界](conversational-approvals.md)，不要用模拟回执或 Agent 复制的回复掩盖这一差异。
