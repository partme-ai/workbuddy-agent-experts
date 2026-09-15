# 芯片能力矩阵（chip-matrix）

read-when：逐芯片核对能力，或评估换芯片。
基线：Espressif 官方产品页与各芯片 get-started 页，走读 **2026-09-02**，不自动更新。置信度：高（除注明中置信行）。

## 主矩阵（全部为基线高置信）

| 芯片 | 架构（官方页原文） | 主频 | 核数 | Wi-Fi 2.4G | BLE | Bluetooth Classic | 802.15.4 |
|---|---|---|---|---|---|---|---|
| ESP32 | Xtensa LX6 | 240 MHz | 双核 | 有 | 有 | 有 | 无 |
| ESP32-S2 | Xtensa LX7 | 240 MHz | 单核 | 有 | **无蓝牙** | 无 | 无 |
| ESP32-S3 | Xtensa LX7 | 240 MHz | 双核 | 有 | 有（无 Classic） | 无 | 无 |
| ESP32-C3 | RISC-V | 160 MHz | 单核 | 有 | 有（无 Classic） | 无 | 无 |
| ESP32-C6 | RISC-V（另有 LP 核 20 MHz） | 160 MHz | 单核 | 有（802.11ax，Wi-Fi 6） | BLE 5 | 无 | 有（Thread/Zigbee） |
| ESP32-H2 | RISC-V | 96 MHz | 单核 | **无 Wi-Fi** | BLE 5 | 无 | 有（Thread 1.3 / Zigbee 认证） |
| ESP32-P4 | RISC-V（LP-Core 40 MHz） | 400 MHz | 双核 | **无片上射频** | — | — | — |

- ESP32-P4 经 **ESP-Hosted/ESP-AT** 使用 C/S 系列芯片作伴生芯片获得无线能力（官方页原文，高置信）。
- 官方 get-started 页对经典 ESP32 的蓝牙未细分版本号——细节按官方页核验，不脑补。

## 新芯片（中置信，只提示存在）

- **ESP32-C5**（单核 RISC-V 240 MHz）、**ESP32-S31**（双核 RISC-V 320 MHz，v6.1 新增 preview 支持）出现在 v6.1 release notes（中置信）。能力细节 **UNVERIFIED**：不做细节描述，以官方选型页为准。

## 高频错误点（基线点名，必须显式检查）

1. **P4 无片上射频**——选 P4 意味着无线要靠伴生芯片方案。
2. **H2 无 Wi-Fi**——只有 BLE + 802.15.4，别用于 Wi-Fi 设备。
3. **S2 无蓝牙**——纯 Wi-Fi 单核。
4. **BLE ≠ Bluetooth Classic**——S3/C3/C6/H2 只有 BLE；要 Classic（如 A2DP 音频）只有经典 ESP32。

## UNVERIFIED：各芯片最低 IDF 版本

基线结论：**未找到官方合并对照表，禁止写死"最低 vX.Y"**。一律按 selection-tree.md 的官方核验法（stable 文档按 target 切换 + release notes）现场确认后再回答。

## 使用约束

- 本矩阵只覆盖"架构 + 核数 + 无线能力"这类官方页明示的硬事实；外设数量、GPIO 总数、封装、温度等级、供货状态等一律引导用户查官方选型页与数据手册，不在本文件内给数。
- 引用本矩阵时带"截至 2026-09-02"。
