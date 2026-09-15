# GE · key-governance（esp32-secureboot 黄金示例）

**徽章**：`S1 Executable Evidence`（ge-key-governance.sh 可在 macOS/Linux 上运行）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-key-governance.sh` | Ed25519 生成/签名/验证/shred 擦除，全流程 5 步，退出码 0 |
| `ge-signing-pipeline.md` | 三阶段签名流水线（rehearsal→试产→放量），eFuse 顺序标注 |

## 与 SKILL.md 映射

- §Pitfalls: "密钥不进仓库/CI" → L48 shred + 5 步治理报告
- §Workflow: rehearsal → pilot → mass production → 三阶段
- §Pitfalls: "先 SB 后 FE" → 顺序说明 + "以官方为准"标注
- §References: key-governance.md → 不变式三原则
