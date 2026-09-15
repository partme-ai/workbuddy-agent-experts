---
name: esp32-debug
license: Apache-2.0
description: Debug crashes and resets on ESP32 with ESP-IDF — a debug-means matrix (JTAG/OpenOCD with ESP-Prog — classic ESP32 has no built-in USB-Serial/JTAG and does NOT support SWD; coredump to flash or UART analyzed via idf.py coredump-info/coredump-debug; runtime GDB stub; idf.py monitor as the baseline channel), the crash handling flow (panic 回溯解读 → coredump 提取 → 符号化调试), and a reset-reason triage table distinguishing 看门狗复位 vs panic vs 掉电/供电问题 with a decision tree for 随机重启. Use when the user says 设备随机重启/莫名复位/死机/Guru 级崩溃, asks 怎么看 panic 回溯/提取 coredump, wants JTAG or OpenOCD setup, or needs to decide JTAG vs coredump vs 串口. Refuses hardware-supply-level conclusions and routes them to fw-hil-testing; refuses to invent wiring pins, JTAG frequencies, or unsupported debug interfaces. For firmware-side fixes shipped via OTA route esp32-ota.
---

# ESP32 Debug（崩溃与复位排障）

调试先分清"软件崩溃还是硬件原因"，再选手段。手段矩阵与命令均出自基线（高置信）；**接线、频率、板级参数一律标"以板与探测器件实测"**，不编造。

## Determine Task Type

1. **设备随机重启/莫名复位**：先分类复位原因（看门狗/panic/掉电）→ [crash-triage](references/crash-triage.md) 决策树 → Workflow B。
2. **已有 panic 现场**：解读回溯 + 提取 coredump → Workflow A。
3. **要断点/单步调试**：手段矩阵选 JTAG/OpenOCD 或 GDB stub → Workflow C + [jtag-openocd](references/jtag-openocd.md)。
4. **怀疑硬件（供电/虚焊）**：软件手段穷尽后 → refusal 路由 `fw-hil-testing`（Hand-off 表）。

## Prerequisites / Preflight

```bash
idf.py --version
idf.py monitor -p <PORT>   # 基线观察通道：先看住现场再谈别的
```

1. **芯片型号**：经典 ESP32 **无内置 USB-Serial/JTAG**，需外部适配器（如 ESP-Prog）才能 JTAG；不支持 SWD（基线高置信）。S 系列芯片内置接口情况按官方芯片文档运行时核验。
2. **手上有什么**：串口线（几乎必有）/ JTAG 探测器（ESP-Prog 类）/ 设备是否在手边、能否复现。
3. **coredump 目的地配置**：flash（data/coredump 分区）还是 UART——决定提取方式（见手段矩阵）。
4. 崩溃现场是否已被后续重启覆盖（coredump 没配置就没了证据）。

## Offline Baseline

- ESP-IDF 基线 = **v6.1**（截至走读 **2026-09-02**，不自动更新）；调试手段引自基线 §10（官方 jtag-debugging 与 core_dump 文档，置信度高）。
- GDB stub 专用文档页 URL：基线未抓到（UNVERIFIED）——只陈述"运行时 GDB stub 存在（CONFIG_ESP_SYSTEM_GDBSTUB_RUNTIME）"，不引具体文档页。
- 板级接线/JTAG 频率：官方页未逐板抓取，**以板与探测器件实测**。

## Contracts（设备契约）

1. **JTAG 事实**：OpenOCD 随 IDF 安装，`openocd -f board/xxx.cfg`；经典 ESP32 走 JTAG，**不支持 SWD**；支持经 JTAG 烧录与 GDB 调试。
2. **Coredump 事实**：panic 时自动保存；目的地 flash（data/coredump 分区）或 UART；分析用 `idf.py coredump-info` / `coredump-debug`。
3. **不编造板级参数**：JTAG 接线引脚、TCK 频率、板上测试点——引用官方板文档或实测，二选一。
4. 复现实验可能反复触发崩溃/重启：对外场设备先备份现场日志与 coredump，再动。

## 调试手段矩阵（基线高置信）

| 手段 | 前提 | 能拿到什么 | 何时选 |
|---|---|---|---|
| `idf.py monitor` | 串口线 | 启动日志、panic 现场 banner 与回溯、复位原因行 | **永远的第一步** |
| Coredump（flash 或 UART） | 分区/配置就位 | 崩溃现场存档，事后 `idf.py coredump-info`/`coredump-debug` 符号化分析 | 现场无法实时盯、随机崩溃 |
| JTAG/OpenOCD + GDB | ESP-Prog 类探测器 | 断点、单步、实时变量 | 复现稳定的逻辑问题 |
| 运行时 GDB stub | CONFIG_ESP_SYSTEM_GDBSTUB_RUNTIME | 无 JTAG 硬件的串口 GDB 调试 | 没有探测器的临时手段 |
| VS Code 官方插件 | 插件环境 | 上述能力图形化（build/flash/monitor/debug） | 团队偏好 IDE |

设置细节读 [jtag-openocd](references/jtag-openocd.md)（接线/频率标"以板与探测器件实测"）。

## 崩溃处理流

```text
复现/等待崩溃
  -> idf.py monitor 观察现场：panic 回溯（哪些任务/哪层代码）
  -> 若已配置 coredump：提取存档
     -> idf.py coredump-info        # 概览：崩溃任务、寄存器、栈
     -> idf.py coredump-debug       # 进 GDB 做符号化调试
  -> 定位到代码位置 -> 修复 -> 回归验证
```

复位原因分类定位表 → [crash-triage](references/crash-triage.md)：看门狗复位、panic、掉电/供电三类，判据与证据链各不相同。

## Capability Boundaries + Hand-off

| User Intent | Skill |
|---|---|
| 已定位是供电/电源设计/硬件问题 | **hand-off**：`fw-hil-testing`（真机在环验证，本 Skill 不下硬件结论） |
| 修复后固件下发 | `esp32-ota` |
| 任务/看门狗相关的并发设计问题 | `esp32-freertos` |
| 工程配置（coredump 分区表等） | `esp32-idf` |
| 外设驱动引发的崩溃 | `esp32-peripherals` |

 refusal 边界：本 Skill 不输出"这就是电源问题"的结论——软件侧只能给出"硬件嫌疑证据"，定论必须真机测量（fw-hil-testing）。

## Workflow A — panic 现场处理

1. `idf.py monitor` 抓现场：记录 panic banner 与回溯原文（先存档再分析）。
2. 解读回溯：崩溃发生的任务与调用层级；回溯地址需与当前固件版本匹配，固件不一致的回溯不可信。
3. 配置了 coredump → `idf.py coredump-info` 概览 → `idf.py coredump-debug` 符号化进 GDB。
4. 修复后按原路径复现验证；无复现条件时明确说"未复现验证"，不声称已修复。

## Workflow B — 随机重启排障（复位原因分类）

1. 按 [crash-triage](references/crash-triage.md) 决策树分类：先从串口启动日志取复位原因证据，再定软件/硬件方向。
2. 软件方向：panic → Workflow A；看门狗 → 检查长阻塞任务/关中断时长（并发细节 → `esp32-freertos`）。
3. 硬件嫌疑（掉电/复位脚毛刺）：收集证据（重启时机与负载相关性等）→ **hand-off `fw-hil-testing`** 实测定论。
4. 随机问题：加日志埋点 + 开启 coredump 存档等复现，不做无证据猜测。

## Workflow C — JTAG/OpenOCD 设置

1. 核对探测器与目标板（Contracts：经典 ESP32 需外部 JTAG，不支持 SWD）。
2. 接线与频率：查官方板文档或实测（[jtag-openocd](references/jtag-openocd.md)，不编造）。
3. 启动：`openocd -f board/<目标板>.cfg`（cfg 名以随 IDF 安装的 OpenOCD 脚本目录实际列表为准）。
4. GDB 连接调试；经 JTAG 烧录亦可用。断点 behaves 异常时先怀疑频率/接线，再怀疑工具链。

## Validation Gates

1. panic 案例：回溯定位到具体代码行，修复后同路径复现不再崩。
2. coredump 链路：人为触发崩溃 → coredump-info 能读到崩溃任务与栈 → coredump-debug 能符号化。
3. 分类正确：一次已知原因的重启（如人为触发看门狗场景）被决策树正确归类。
4. JTAG 链路：断点命中、单步、变量查看各验证一次。
5. 无真机/无现场：结论一律标 `Build Verification Only` / `Pending HIL`。

## Pitfalls

1. **不要**把"随机重启"未经分类就归因软件或硬件——先走复位原因决策树。
2. **不要**给经典 ESP32 排 SWD 调试任务——它不支持 SWD，走 JTAG。
3. **不要**编造 JTAG 接线/TCK 频率/board cfg 名——查官方或实测（Pending HIL）。
4. **不要**用与目标设备不同版本的 ELF 去符号化 coredump——地址对不上，结论全错。
5. **不要**在没配 coredump 的产品里追随机崩溃——证据早被下一次重启覆盖；先补配置再等复现。
6. **不要**直接下"供电问题"结论——给出嫌疑证据后 hand-off `fw-hil-testing` 测量定论。
7. **不要**引用 GDB stub 的"专用文档页"——基线未抓到（UNVERIFIED），只陈述 Kconfig 事实。

## Official Sources

- [JTAG 调试](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/jtag-debugging/index.html)
- [Core Dump 文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/core_dump.html)
- [idf.py 工具](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/tools/idf-py.html)
- [VS Code ESP-IDF 插件](https://github.com/espressif/vscode-esp-idf-extension)

## Privacy

coredump、串口日志可能包含网络凭据、设备标识与用户数据：分享/归档前脱敏；本 Skill 不采集、不外发诊断数据；诊断包外发（如给上游组件报 issue）前须经用户确认并清理敏感内容。
