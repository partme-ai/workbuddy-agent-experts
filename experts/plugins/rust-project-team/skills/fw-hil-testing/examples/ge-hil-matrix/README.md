# GE · hil-matrix（fw-hil-testing 黄金示例）

**徽章**：`B0 Build Verification Only`（矩阵文档，需真机验证）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-hil-matrix-openwrt.md` | OpenWrt 网关 10 行验收矩阵（上电→DLNA→NATS补推→72h） |
| `ge-hil-matrix-esp32.md` | ESP32 MCU 10 行验收矩阵（上电→OTA回滚→深睡→SecureBoot→电流） |
| `ge-gate-flow.md` | 商业门禁 G1-G4 流程（样机→单渠道→多渠道→售后） |

## 与 SKILL.md 映射

- §Evidence Contract: "验收矩阵模板" → 10 行 × 7 列（验收项/前置/操作/观察/预期/证据/徽章）
- §Workflow A (OpenWrt): 网关型 HIL → ge-hil-matrix-openwrt.md
- §Workflow B (ESP32): MCU 型 HIL → ge-hil-matrix-esp32.md
- §Pitfalls: "µA 数值 UNVERIFIED" → ESP32 矩阵 #10 标注"以实测为准"
- §References: completion-badges.md → B0/B1/B2 三级徽章
- §References: evidence-matrix.md → G1-G4 门禁映射

## 验证

```bash
grep -c "^|" ge-hil-matrix-openwrt.md  # 应有 ≥12 行（含表头+分隔）
grep -c "^|" ge-hil-matrix-esp32.md    # 同上
```
