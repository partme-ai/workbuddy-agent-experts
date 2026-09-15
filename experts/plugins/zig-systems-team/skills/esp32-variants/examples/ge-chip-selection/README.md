# GE · chip-selection（esp32-variants 黄金示例）

**徽章**：`B0 Build Verification Only`（文档类）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-chip-selection.md` | 7 芯片对照表 + 决策树 mermaid + UNVERIFIED 标注 |

## 与 SKILL.md 映射

- §Workflow: "选型决策树" → mermaid flowchart
- §Pitfalls: "各芯片最低 IDF 版本 UNVERIFIED" → 表头注释
- §Pitfalls: "ED25519 归属 UNVERIFIED" → 关键说明第 3 条
- §References: chip-matrix.md → 7 芯片架构/无线能力
- §References: selection-tree.md → 决策树逻辑
