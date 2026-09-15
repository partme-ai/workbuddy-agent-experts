---
name: esp32-peripherals
license: Apache-2.0
description: Choose and wire ESP-IDF peripheral drivers for GPIO, I2C, SPI, UART, ADC, PWM (LEDC), and RMT — when to use each peripheral, the v6.x new-style componentized driver direction (e.g. driver/i2c_master.h from esp_driver_i2c, verified on official stable docs 2026-09-02) versus legacy drivers removed in v6.0, bus configuration (I2C address/speed, SPI mode, UART baud), and the hardware contract that pin numbers, mux options, pull-up availability, and strapping pin values must come from the chip datasheet or board schematic — never fabricated. Use when users mention 引脚/GPIO, I2C/SPI/UART/传感器接线, ADC 采样, PWM/LEDC/呼吸灯, RMT 红外/彩灯, driver headers like i2c_master.h, or ask which pins to use on a given ESP32 chip. REFUSES to quote default pin numbers for a chip from memory — routes to datasheet + menuconfig/runtime verification. Hand off concurrency around drivers to esp32-freertos, crash analysis to esp32-debug, and project/build issues to esp32-idf.
---

# ESP32 外设与驱动（esp32-peripherals）

本 Skill 决定"用哪个外设、哪个驱动接口、接到哪个引脚"。**硬件契约优先：引脚/复用/上拉/Strapping 一律以芯片 datasheet 或板原理图为准，禁止编造。** 驱动接口以 v6.x 新式组件化方向为准，legacy 驱动在 v6.0 已移除（基线高置信）。

## Determine Task Type

1. **选外设/驱动接口** — 需求映射到 GPIO/I2C/SPI/UART/ADC/PWM(LEDC)/RMT，并确认 v6.x 新式接口 → 决策表。
2. **接线与引脚分配** — 查 datasheet/原理图定引脚与上拉 → 走硬件契约流程（Workflow 1）。
3. **总线调不通** — I2C 无 ACK、SPI 花屏、UART 乱码 → Workflow 2（先查电气与配置，再查代码）。
4. **并发问题**（ISR 与驱动共享数据）→ 移交 `esp32-freertos`；**崩溃取证** → `esp32-debug`。

## Preflight（先运行时核验）

```bash
idf.py --version                          # v6.x → 新式驱动方向；v5 → 提示迁移路径
grep -rn "#include \"driver/" main/       # 工程现有驱动头文件（发现 legacy 痕迹）
grep -m1 "CONFIG_IDF_TARGET" sdkconfig    # 芯片 target，与实物核对
```

- target 与芯片实物/原理图核对后再谈引脚。
- 准确头文件名以**本机 IDF 源码树**与官方 API 参考为准；本文只标注已核验的方向。

## Offline Baseline

- 驱动迁移事实以日期化基线为准：ESP-IDF v6.1，走读 **2026-09-02**，不自动更新。
- 基线高置信：v6.0 移除 legacy 驱动（点名 ADC、I2S、Timer 等）；`driver/i2c_master.h`（`esp_driver_i2c` 组件）为官方 stable 文档当日核验的 I2C master 新接口。
- 其余外设头文件名未逐个抓取——引用时标"运行时核验"，不凭记忆补全。

## Contracts（硬件契约——本 Skill 红线）

- **引脚编号与复用**：一律读目标芯片的 datasheet / 技术参考手册 / IO MUX 表，或板原理图；**不确定即停，禁止给"常见值"**。
- **Strapping 引脚**：其上电默认值与外部上/下拉影响启动模式——**禁止编造 Strapping 引脚值**；涉及时先查 datasheet 再接线。
- **上拉/下拉**：某 GPIO 是否可内部上拉、驱动能力多大，以 datasheet 为准；I2C 是否需要外部上拉按总线电气计算。
- **器件侧**：I2C 从机地址、SPI mode/极性、UART 波特率与电平，以外设器件手册为准（3.3V/5V 电平适配提醒用户核对）。

## 外设决策表

| 外设 | 何时用 | v6.x 驱动方向（详见 bus-quickref / adc-caveats） |
|---|---|---|
| GPIO | 按键/LED/简单开关量、边沿中断 | 通用 GPIO 接口；头文件名运行时核验 |
| I2C | 低速传感器/EEPROM，多从机共总线 | 新式 master：`driver/i2c_master.h`（esp_driver_i2c，已核验） |
| SPI | 高速器件（屏/Flash/ADC），全双工 | 新式主驱动方向；头文件名运行时核验 |
| UART | 与外部模块/调试串口通信 | 通用 UART 驱动 + `esptool`/monitor 依赖的 console 口分开 |
| ADC | 读模拟量（电位器/电池电压） | legacy ADC 已在 v6.0 移除——用新接口（见 adc-caveats，标核验） |
| PWM | 调光/舵机/蜂鸣器 → LEDC | LEDC 外设；头文件名运行时核验 |
| RMT | 红外收发、WS2812 彩灯、精确位时序 | RMT 外设（精确时序场景优先于 GPIO 翻转）；标核验 |

## Capability Boundaries + Hand-off

| User Intent | Skill |
|---|---|
| 工程骨架/构建烧写/分区表 | `esp32-idf` |
| IDF 版本升级 / v5→v6 工程迁移 | `esp32-idf` |
| 驱动任务与 ISR 并发模型 | `esp32-freertos` |
| 采样异常定位后的崩溃取证 | `esp32-debug` |
| 睡眠期间的引脚保持/功耗 | `esp32-lowpower` |
| 芯片有没有该外设（选型层） | `esp32-variants` |
| 总线时序实测（逻辑分析仪/示波器） | `fw-hil-testing` |

## Workflow 1：接线与引脚分配

1. 确认 target 与芯片实物一致（Preflight）。
   - 引脚落点：核验后的引脚号必须**显式写入驱动初始化配置/参数**（或 menuconfig），不得留空交由默认值猜测。
2. 打开该芯片 datasheet 的 IO MUX/引脚定义章节，列出候选引脚；记录哪些是 Strapping 引脚并避开。
3. 对照板原理图确认引脚实际连接与上/下拉电阻现状。
4. 把"引脚号 → 外设 → 电气条件"写成清单给用户确认，再写代码。
5. 若 datasheet 与网上教程冲突：**以 datasheet 为准**，并提醒教程可能对应不同芯片。

## Workflow 2：总线调不通

1. **先电气后代码**：供电、共地、上拉、电平匹配、线长。
2. I2C 无 ACK：核对 7 位/8 位地址写法、速率是否超器件上限、总线是否被上拉拉起（有条件用逻辑分析仪看波形 → fw-hil-testing）。
3. SPI 异常：核对 mode（CPOL/CPHA）与字节序、片选时序、速率降档试验。
4. UART 乱码：两端波特率/校验位一致；确认测量的是同一 TTL 口而非 RS232 电平。
5. 代码侧排查：确认 include 的是 v6.x 新式驱动头（legacy 头在 v6.0 已移除，见 [bus-quickref](references/bus-quickref.md)）。

## Validation Gates

- `idf.py build` 通过，无 legacy 头文件警告。
- 引脚清单与 datasheet/原理图逐条对上；Strapping 引脚未被误用。
- 总线通信有证据：器件应答/正确数据/示波器波形，三者之一才算通。
- 无硬件证据时标注 `Build Verification Only`。

## Pitfalls

1. **不要**回答"某芯片的 I2C 默认引脚号"这类问题而不核验——ESP-IDF 多数引脚可矩阵映射，没有跨板统一的"默认"，必须 datasheet + 用户原理图确认（典型 refusal 场景）。
2. **不要**在 v6.x 工程里继续用 legacy 驱动 API（ADC/I2S/Timer 等已在 v6.0 移除）。
3. **不要**编造 Strapping 引脚默认值或"随便挑个 GPIO"——上电状态取决于这些脚。
4. **不要**把 I2C 地址的 7 位/8 位写法混用导致"地址不存在"的假故障。
5. **不要**在 ISR 里直接调阻塞的总线传输——并发模型移交 `esp32-freertos`。

## Official Sources

- [ESP-IDF API 参考（外设）](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/index.html)
- [I2C（含 driver/i2c_master.h）](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/i2c.html)
- [ESP-IDF Migration Guides](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/migration/index.html)
- [Espressif 官方选型页](https://www.espressif.com/en/products/socs)

## Privacy

本 Skill 不采集、不外发用户数据或器件凭据；引脚与原理图信息仅用于当前任务的本地分析；访问官方链接遵守用户环境网络策略。
