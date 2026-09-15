# 选型决策树与核验方法（selection-tree）

read-when：需求明确后收敛候选芯片；或需要回答"这块芯片最低要哪个 IDF 版本"。
基线：走读 2026-09-02。

## 决策树

```text
需要什么无线能力？
├── Thread / Zigbee（802.15.4）
│   ├── 还要 Wi-Fi → ESP32-C6（802.11ax + BLE 5 + 802.15.4）
│   └── 不需要 Wi-Fi → ESP32-H2（BLE 5 + 802.15.4，Thread 1.3 / Zigbee 认证）
├── Wi-Fi + 蓝牙
│   ├── 要 Bluetooth Classic（如经典音频）→ 经典 ESP32（唯一有 Classic）
│   └── 只要 BLE
│       ├── 成本敏感 / 单核够用 → ESP32-C3（RISC-V 160 MHz）
│       ├── 要 AI 向量指令 / 双核算力 → ESP32-S3
│       └── 双频 Wi-Fi 等新需求 → 查官方（C5 细节 UNVERIFIED）
├── 只 Wi-Fi、无蓝牙 → ESP32-S2（单核）
├── 无线主机（高性能应用核，Wi-Fi 靠伴生）→ ESP32-P4 + ESP-Hosted/ESP-AT
└── 都不要无线 → 按算力/核数在 C3/H2/P4 等里比（仍需按官方页核验）
```

收敛次序：**射频硬过滤 → 算力/核数 → 成本/封装**。硬过滤淘汰的芯片不再进决策树。

## "最低 IDF 版本"运行时核验法（禁止背答案）

基线结论：官方**没有**合并的"芯片 × 最低 IDF 版本"对照表（UNVERIFIED）。核验三步：

1. **stable 文档按 target 切换**：打开 `https://docs.espressif.com/projects/esp-idf/en/stable/<target>/get-started/`（`<target>` 如 `esp32c3`、`esp32p4`）。该芯片在 stable 文档有独立 get-started 页 → 当前 stable 支持它；没有 → 说明 stable 不支持或尚未正式支持。
2. **release notes 查新增支持**：`https://github.com/espressif/esp-idf/releases`——新增/preview 支持（如 v6.1 提及 S31）只在发布说明中体现；引用时带发布日期。
3. **本机实测**：`idf.py set-target <target>` 成功生成 sdkconfig 且 `idf.py build` 通过，才算"本机这个 IDF 版本支持"。文档支持 ≠ 本机版本支持。

回答模板："官方无对照表；按 stable 文档与 release notes 核验，该芯片在 vX.Y（截至 YYYY-MM-DD）…；本机请以 `idf.py set-target` 实测为准。"

## 常见组合建议（需求 → 起点）

| 需求 | 起点 | 备注 |
|---|---|---|
| 低成本 Wi-Fi+BLE 单核 | C3 | RISC-V，量产最常见起点 |
| AI/端侧推理（向量指令）+ Wi-Fi+BLE | S3 | 双核 LX7 |
| Thread/Zigbee 网关或路由器 | C6 | 兼有 Wi-Fi 6 |
| Thread/Zigbee 纯终端（无 Wi-Fi） | H2 | 96 MHz，功耗与成本优先 |
| 高性能应用核 / 多媒体 | P4 | 双核 RISC-V 400 MHz；无线配伴生芯片 |
| 经典蓝牙音频等 Classic 场景 | 经典 ESP32 | 唯一带 Classic |

## 反幻觉提示

- 组合建议只是"起点"，最终以官方选型页与数据手册核对（外设/GPIO/封装本包不给数）。
- 新芯片（C5/S31 等）只提示存在；细节 UNVERIFIED，不描述。
