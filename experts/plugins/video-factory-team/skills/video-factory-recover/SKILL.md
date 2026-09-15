---
name: video-factory-recover
description: Use when a Video Factory analysis, rough cut, review render, or final render was interrupted and the durable ledger must determine the only legal next action.
---

# Recover a Video Factory job

## When to use · 何时恢复

仅在分析、粗剪、同步审阅或终版任务被中断，且已有可读取的持久台账或证据回执时使用。没有台账
时先报告缺失项，不猜测已经完成的步骤。

## Workflow · 恢复流程

1. 执行 `bin/video-factory status <ledger.json>`，确认 state、revision、stage 和历史。
2. 执行 `bin/video-factory recover <ledger.json>`，只读取恢复前沿，不直接重新渲染。
3. 重新校验 capability、plan/edit hash、stage、round、素材哈希和已有分段回执。
4. 仅当 nextAction 为 `resume_pending` 且幂等键一致时，用同一计划和批准继续 run。
5. Failed 项必须修复原因并创建新 round；不得用原参数自动重试。

`Completed` 分段不会重做；回执缺失或哈希变化的分段不能冒充完成。旧粗剪、同步审阅版、终版和
EditDecision 均保留。若台账损坏，报告具体文件和最后可验证回执，不猜测状态、不删除工作目录。

常见恢复：进程中断 → 继续 Pending；Chrome 缺失 → 保留普通粗剪并跳过增强审阅；素材变化 →
旧批准失效并创建新 round；确定性质量失败 → 修复计划后重新报价。

## Capability boundaries · 能力边界

能恢复同一幂等键下的 Pending 工作；需要原计划、批准、素材和回执仍有效；不重试 Failed、不覆盖
旧产物、不删除工作目录、不从损坏台账臆造状态。

## Validation and gotchas · 校验与陷阱

任何 Failed 优先返回 `new_round_required`，即使还有 Pending；只有 Running + Pending 才返回
`resume_pending`。恢复前重算素材和分段哈希，回执被篡改则不能复用。

参见 [操作与恢复](../video-factory-use/references/operations.md) 和
[示例与 FAQ](../video-factory-use/references/examples-and-faq.md)。
