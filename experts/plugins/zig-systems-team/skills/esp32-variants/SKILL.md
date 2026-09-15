---
name: esp32-variants
license: Apache-2.0
description: Select the right ESP32-family chip for a project — compare architecture (Xtensa LX6/LX7 vs RISC-V), core count, and Wi-Fi / BLE / 802.15.4 radio capabilities across ESP32, S2, S3, C3, C6, H2, P4; apply a decision tree (low-cost unicore → C3, AI vector instructions → S3, Thread/Zigbee → C6/H2, dual-core high performance → S3/P4); and verify minimum supported ESP-IDF versions at runtime instead of fabricating them. Use when users are choosing a chip/module (选型), comparing ESP32 variants, asking which ESP32 to use for Thread, Zigbee, Wi-Fi 6, BLE-only, or AI workloads, or evaluating a migration to another chip in the family. Do NOT state per-chip minimum ESP-IDF versions (UNVERIFIED — give the official verification method instead). Hand off project scaffolding to esp32-idf, low-power design to esp32-lowpower, and secure boot, provisioning, or peripherals to their dedicated esp32-* skills.
---

# ESP32 家族选型（esp32-variants）

本 Skill 只做芯片能力对比与选型决策。**高频错误点（基线明确）：P4 无片上射频、H2 无 Wi-Fi、S2 无蓝牙。** 各芯片"最低 IDF 版本"为 UNVERIFIED——本 Skill 拒绝写死，只给官方核验方法。

## Determine Task Type

1. **从零选型** — 需求（无线/算力/核数/成本）→ 芯片 → 走 Workflow。
2. **换芯片评估** — 既有工程迁到别的 ESP32 芯片 → 先按矩阵排除硬伤（射频/核数），再交 `esp32-idf` 评估工程迁移。
3. **识别手头芯片** — 用户描述板子/模组，帮助确认 target → 与实物丝印核对，禁止凭描述猜。
4. **芯片已定** → 直接移交 `esp32-idf`（工程）或对应专项 Skill。

## Preflight（先运行时核验）

```bash
idf.py --version                              # 本机 IDF 版本
grep -m1 "CONFIG_IDF_TARGET" sdkconfig 2>/dev/null   # 已有工程的 target
```

- 问清需求三要素：**要什么无线能力（Wi-Fi/BLE/802.15.4/都不用）、算力与核数、成本与封装约束**。
- 候选芯片能否被本机/目标 IDF 支持：按 [selection-tree](references/selection-tree.md) 的官方核验法确认，**不凭记忆**。

## Offline Baseline

- 芯片能力事实以日期化基线为准（官方产品页与各芯片 get-started 页），走读 **2026-09-02**，不自动更新。
- 新芯片（如 ESP32-C5、ESP32-S31）在 v6.1 release notes 中有提及（**中置信**），能力细节 UNVERIFIED——只提存在，不做细节描述，以官方选型页为准。

## Contracts

- **需求必须与用户确认**，不得按"常见场景"替用户决定无线能力（例如默认给 BLE）。
- 射频能力是硬边界：矩阵说不带的（P4 射频、H2 Wi-Fi、S2 蓝牙）就是不带；"外挂/伴生芯片"方案要显式说明（P4 经 ESP-Hosted/ESP-AT 用 C/S 系列作伴生）。
- 选型结论落地前，芯片的封装/外设/供货由用户按官方选型页与模组数据手册确认——本 Skill 不替用户锁型号。

## Capability Matrix（基线高置信，详见 chip-matrix）

| 芯片 | 架构 | 无线 |
|---|---|---|
| ESP32 | 双核 Xtensa LX6 240 MHz | Wi-Fi 2.4G + Bluetooth（Classic+BLE） |
| ESP32-S2 | 单核 Xtensa LX7 240 MHz | 仅 Wi-Fi，**无蓝牙** |
| ESP32-S3 | 双核 Xtensa LX7 240 MHz | Wi-Fi 2.4G + 仅 BLE |
| ESP32-C3 | 单核 RISC-V 160 MHz | Wi-Fi 2.4G + 仅 BLE |
| ESP32-C6 | 单核 RISC-V 160 MHz（+LP 核） | Wi-Fi 6 (802.11ax) + BLE 5 + 802.15.4（Thread/Zigbee） |
| ESP32-H2 | 单核 RISC-V 96 MHz | **无 Wi-Fi**；BLE 5 + 802.15.4（Thread 1.3 / Zigbee 认证） |
| ESP32-P4 | 双核 RISC-V 400 MHz（+LP 核） | **无片上射频**；经 ESP-Hosted/ESP-AT 配伴生芯片 |

## Capability Boundaries + Hand-off

| User Intent | Skill |
|---|---|
| 选定芯片后建工程/迁移构建 | `esp32-idf` |
| 低功耗续航设计（电池设备选型后） | `esp32-lowpower` |
| Thread/Zigbee 协议栈实现细节 | 官方 ESP-IDF 文档（超出本包范围时说明） |
| 安全启动/配网/外设/并发 | `esp32-secureboot` / `esp32-wifi-provision` / `esp32-peripherals` / `esp32-freertos` |
| Rust no_std（esp-hal） | 包外 `rust-skills/rust-embedded`（refuse 并移交） |

## Workflow：选型四步

1. **列需求**：无线（含协议版本）、算力、核数、功耗、成本；逐项确认。
2. **硬过滤**：按矩阵排除射频硬伤（例：要 Thread/Zigbee → 只剩 C6/H2；要 Wi-Fi+蓝牙 Classic → 只有经典 ESP32）。
3. **决策树收敛**（见 selection-tree.md）：单核低成本→C3；AI 向量指令→S3；Thread/Zigbee→C6/H2；双核高性能→S3/P4。
4. **运行时核验**：对候选芯片执行官方支持核验（selection-tree.md 的查法），确认本机 IDF 版本可用，再移交 `esp32-idf` 建工程。

## Validation Gates

- 选型结论必须能回指矩阵某一行 + 决策树某条路径，且需求三要素逐项对上。
- "该芯片最低需要 IDF vX.Y"这类结论**不得出现**——只允许输出核验方法与核验结果。
- 涉及"实际能跑"的说法：无硬件证据时标注 `Pending HIL`。

## Pitfalls

1. **不要**写死各芯片的最低 IDF 版本号——基线明确 UNVERIFIED，官方无合并对照表，只给核验法。
2. **不要**说"P4 可以自己连 Wi-Fi"——P4 无片上射频，必须配伴生芯片（ESP-Hosted/ESP-AT）。
3. **不要**把 H2 当 Wi-Fi 芯片、把 S2 当蓝牙芯片——基线高频错误点。
4. **不要**按"名字像"归组（C3 与 C6 能力差异大：802.11ax 与 802.15.4 只有 C6 有）。
5. **不要**用中置信条目（C5/S31）给结论——只提示"存在更新芯片，细节以官方为准"。

## Official Sources

- [Espressif ESP32 产品选型（SoC 矩阵）](https://www.espressif.com/en/products/socs)
- [ESP-IDF stable 文档（按 target 切换）](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/)
- [ESP-IDF Releases](https://github.com/espressif/esp-idf/releases)

## Privacy

本 Skill 只做本地需求分析与静态对比，不采集、不外发用户数据；访问官方链接遵守用户环境网络策略。
