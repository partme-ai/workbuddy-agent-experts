# GE · task-routing 10 条决策记录（fw-core 黄金示例）

**徽章**：`B0 Build Verification Only`（文档类）

---

## 决策记录

| # | 用户 Prompt | 任务分型 | 路由技能 | 为什么路由 | 边界 |
|---|---|---|---|---|---|
| 1 | "给我的 N1 刷 TinyNAS 固件" | Linux 网关固件 | `openwrt-amlogic-remake` | "N1" + "刷固件" → Amlogic S905D remake 链路 | — |
| 2 | "ESP32-C3 项目怎么加 OTA" | MCU 固件 | `esp32-ota` | "OTA" + 芯片型号 → OTA 专属技能 | 不路由 esp32-idf（已用 3+ 年的分工边界） |
| 3 | "帮我编一个 s905d 的 DTB" | **Refusal** | `openwrt-amlogic-remake` → 拒绝编造 | DTB 编造属于反幻觉红线 | 路由上游板型库/运行时核验 |
| 4 | "macOS 上怎么装 xtensa-esp-elf-gcc" | 工具链 | `fw-toolchain` → hand-off `esp32-idf` | 工具链由 IDF 托管，禁 apt 装 | — |
| 5 | "没有 N1，先验证镜像能不能启动" | 模拟验证 | `fw-emulation` | "验证" + "启动" + "无板" → QEMU 冒烟 | 不路由 fw-hil-testing（需要真机） |
| 6 | "Rust 写一个 no_std 嵌入式驱动" | **Refusal（包外）** | → `rust-skills/rust-embedded` | no_std 属 Rust 生态，本包不覆盖 | 路由既有 rust-skills |
| 7 | "OpenWrt 镜像做完后怎么发布到渠道" | 发布门禁 | `fw-release-gate` | "发布" + "渠道" → 发布门禁 | — |
| 8 | "升级后设备又跑回旧版本了" | 排障 | `esp32-ota` | "升级" + "回旧版" → OTA 回滚（PENDING_VERIFY 未确认） | — |
| 9 | "插座量产怎么配网" | MCU 配网决策 | `esp32-wifi-provision` | "量产" + "配网" → 统一配网选型 | — |
| 10 | "QEMU 跑通了能不能直接发货" | 模拟验证 | `fw-emulation` → 拒绝发货 | "QEMU" 触发，但"发货"属于 HIL 验收 → 手动转交 `fw-hil-testing` | Boot Verified ≠ HIL Verified |

## 统计

- 任务类型覆盖：Linux 网关(1) / MCU(4) / no_std refusal(1) / 模拟验证(2) / 发布门禁(1) / refuse+handoff(1)
- 边界案例：3 条（refusal 编 DTB、refusal no_std、QEMU ≠ 发货）
- 路由歧义：#10 由 fw-emulation 正确拦截并转交 fw-hil-testing

## 验证

```bash
python3 -c "import json;json.load(open('ge-routing-decisions.json'))" && echo "JSON OK"
```
