# GE · task-routing（fw-core 黄金示例）

**徽章**：`B0 Build Verification Only`（文档类）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-routing-decisions.md` | 10 条路由决策（4 种任务类型 + 3 条边界案例 + 2 条 refusal） |
| `ge-routing-decisions.json` | 结构化版本（供评估器消费） |

## 与 SKILL.md 映射

- §Determine Task Type: 4 型分型（Linux 网关/MCU/no_std/refusal/模拟）
- §Hand-off 路由表: 19 行全覆盖 → 10 条示例抽样验证
- §Prerequisites: "构建成功≠硬件可用" → #10 refusal（QEMU ≠ 发货）
- §Privacy: no_std refusal → handoff 到包外 rust-skills

## 验证

```bash
python3 -c "import json;json.load(open('ge-routing-decisions.json'))" && echo "JSON OK"
```
