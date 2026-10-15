# 完整本地流程示例 / Full local workflow fixture

```bash
python3 examples/full-workflow/run.py --output-dir /tmp/draftcut-full-example --initialize-composition
```

需要已安装依赖、Node/Python/FFmpeg；输出使用新空目录。没有云调用、私有源、付费 API 或生产密钥。

原稿：`嗯我们支持支持三十不对四十个用户不是四十万Kimi很很重要`。
精炼稿：`我们支持四十个用户不是四十万Kimi很很重要`。

原声源是按词标记的确定性音调，时间戳手写；它使采样拼接、保护词、字幕和门禁可复现，不冒充真实口播／ASR。示例用独立临时 fixture 身份模拟两次批准。生产代码只允许这份已知 PCM 与词表进入示例路径，不接受真实录音的 `example_only` 自声明。

命令实际生成源、完整编辑决定、审听代理、差异稿、第一道回执、正式精炼音频/SRT、导演脚本、第二道回执与可初始化的工程。初始化仍是 scaffold；实际 MG、连续预览和导出须按仓库 Skill 在该输出项目中完成，不能把技术测试当作创作者成片。

Run from a fresh path. The two receipts are synthetic fixture decisions, not human approvals. Never copy them into a real project. See [human approval setup](../../docs/approvals.md) and [migration](../../docs/audio-first-migration.md).
