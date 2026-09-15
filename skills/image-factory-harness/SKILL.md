---
name: image-factory-harness
description: Image Factory CLI invocation spec for WorkBuddy - probe, prompt-search, validate-plan, quote, run, evaluate, optimize, recover and status subcommands, destination/generation-dir rules, budget gates and the reject-optimize-rerun loop. Read this before generating any image.
---

# 图片工厂调用规范（WorkBuddy）

执行通道是本插件随附的 CLI：`<插件根>/bin/image-factory`（shell 入口）。先 `ls` 确认插件根，
再执行；所有命令支持 `--json` 取机器可读输出。

**依赖披露（事实，不是缺陷）**：该 CLI 底层经**本地 Codex CLI** 出图，消耗的是 **Codex 账户的图片配额**，
生成模型由 Codex 平台选择（不可通过参数指定）。WorkBuddy 智能体以子进程方式驱动它，
需要本机已安装 Codex CLI。

## 1. 子命令面

```
image-factory probe                 # 环境与能力探测（第一步永远先跑它）
image-factory prompt-search <词>    # 提示词库检索
image-factory validate-plan <plan>  # 计划静态校验
image-factory quote <plan>          # 估算（预算/配额门禁在这里暴露）
image-factory run <plan>            # 生成（消耗配额，前置于已验证计划）
image-factory evaluate <产物>       # 主观+程序化评测（主色/留白等）
image-factory optimize <产物/计划>  # 拒收后的优化建议
image-factory recover               # 失败恢复
image-factory status                # 任务状态
```

## 2. 硬规则（来自上游验证记录）

- **`--generation-dir` 与 `--destination` 分离**：plan/job 工作目录不得放进 destination 产物树。
- destination 以外不落正式产物；quote 超预算就不 run，如实上报。
- 评测闭环是常态：`evaluate` 拒收 → `optimize` → 改计划 → 再 `run`，不是异常路径。

## 3. 标准工作流

1. `probe` 确认环境可用；不可用就停，报探测输出。
2. `prompt-search` 找提示词基线 → 写 plan → `validate-plan` → `quote`。
3. `run` → `evaluate`：主色/留白/构图按计划阈值判定，不过就走优化闭环。
4. 交付时列出：计划参数、产物路径、评测数值、消耗与剩余配额、未验证项。

## 4. 纪律

- 4 个 `image-factory-*` 技能已随插件分发：run/judge/recover/use 各有契约细节，**动手前读对应技能**。
- 每一步的 JSON 输出是事实来源；叙述与 JSON 冲突时以 JSON 为准。
- 配额是硬约束：任何"再试一次"之前先看 `quote`/`status`。
