# 计划结构验证 / Plan structure validation

```bash
python3 examples/plan-validation/run.py
```

这份无媒体的合成输入只验证画布、完整 cue 时间线、创意字段和 v2 工作流结构，不能批准生产。脚本输出结构通过、旧布尔批准拒绝和时间线缺口拒绝。

The pure validator does not read media or authenticate a human. The production `scripts/validate_plan.py --plan ...` additionally checks both current signed approvals and the actual refined source. To exercise the full state machine and audio generation, use [the complete fixture](../full-workflow/README.md).
