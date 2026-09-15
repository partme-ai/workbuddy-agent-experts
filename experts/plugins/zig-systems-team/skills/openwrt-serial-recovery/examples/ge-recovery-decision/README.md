# GE · recovery-decision（openwrt-serial-recovery 黄金示例）

**徽章**：`B0 Build Verification Only`（文档类）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-recovery-decision-tree.md` | 三级梯度（U盘→串口→编程器）、先软后硬原则、排障表 |

## 与 SKILL.md 映射

- §Workflow: "三条恢复梯度" → L1/L2/L3 逐级
- §Pitfalls: "不要跳级操作" → 先软后硬原则表
- §Pitfalls: "具体板子引脚/短接点禁止编造" → L3 明确声明 Pending HIL
- §Mandatory Contracts: "UART 115200 8N1 为常见值" → L2 标注"以板实测为准"
