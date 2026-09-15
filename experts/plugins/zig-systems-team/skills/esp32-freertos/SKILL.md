---
name: esp32-freertos
license: Apache-2.0
description: Design, review, and troubleshoot concurrent code on the ESP-IDF FreeRTOS variant (IDF FreeRTOS, a modified Vanilla FreeRTOS v10.5.1 kernel as of 2026-09-02) — task creation, queue/semaphore/mutex/software-timer patterns, stack sizing in BYTES (not words like upstream FreeRTOS), priorities (default CONFIG_FREERTOS_MAX_PRIORITIES=25, configurable — verify against sdkconfig), xTaskCreatePinnedToCore and SMP dual-core pinning on ESP32/S3/P4/H4 (PRO_CPU/APP_CPU), portMUX critical sections, and stack-overflow/watchdog triage. Use when users mention xTaskCreate/xTaskCreatePinnedToCore, 任务/队列/信号量/互斥/软件定时器, 栈溢出, 任务优先级, 双核/绑核, PRO_CPU/APP_CPU, portMUX, or FreeRTOS concurrency inside an ESP-IDF project. Route pin-level peripheral drivers to esp32-peripherals, crash/coredump analysis to esp32-debug, project and sdkconfig issues to esp32-idf, and sleep/low-power design to esp32-lowpower.
---

# ESP-IDF FreeRTOS 并发（esp32-freertos）

本 Skill 处理 ESP-IDF 自带的 **IDF FreeRTOS**（基于 Vanilla FreeRTOS v10.5.1 修改的内核，基线高置信），不是上游原版 FreeRTOS。任务划分、同步原语、栈/优先级、双核绑核。**两个最容易踩的差异：栈单位是字节；优先级上限可配（默认 25，以 sdkconfig 为准）。**

## Determine Task Type

1. **并发结构设计** — 划分任务、选队列/信号量/定时器 → Workflow 1。
2. **栈/优先级调参** — 栈溢出嫌疑、优先级反转嫌疑 → Workflow 2（栈单位=字节）。
3. **双核/SMP 问题** — 绑核、核间竞争、PRO_CPU/APP_CPU → Workflow 3，读 [smp-pinning](references/smp-pinning.md)。
4. **崩溃现场**（panic/backtrace/coredump）→ 移交 `esp32-debug`。
5. **驱动/引脚层的并发**（ISR 与外设驱动交互）→ 移交 `esp32-peripherals`。

## Preflight（先运行时核验）

```bash
idf.py --version                          # IDF 版本决定内核版本
grep -E "CONFIG_FREERTOS_(UNICORE|MAX_PRIORITIES)" sdkconfig
grep -nE "xTaskCreate|PinnedToCore|xQueue|Semaphore|portMUX" main/*.c
```

- 确认本项目是单核还是双核运行（`CONFIG_FREERTOS_UNICORE`）。
- 确认本项目实际的优先级上限（`CONFIG_FREERTOS_MAX_PRIORITIES`）——**不要按 25 回答，按 sdkconfig 回答**。
- 记录现存任务的栈参数与绑核情况，改动前先复现问题。

## Offline Baseline

- IDF FreeRTOS 事实以日期化基线为准：**基于 Vanilla FreeRTOS v10.5.1 修改**，走读 **2026-09-02**，不自动更新。
- SMP 双核目标：**ESP32、ESP32-S3、ESP32-P4、ESP32-H4**（Core 0=PRO_CPU / Core 1=APP_CPU）；S2/C3 等单核恒为 unicore。
- 上游 FreeRTOS v10.5.1 之后的语义变化，以官方文档与本机 sdkconfig/源码为准。

## Contracts

- 芯片核数与 target 与实物/原理图核对后再谈绑核；单核芯片讨论 PinnedToCore 无意义。
- 栈大小、优先级、队列长度是**项目决策**：以代码与 sdkconfig 现状为准，禁止建议时编造"推荐值"却声称是官方值。
- 改并发参数会改变时序行为：每次只改一个维度（栈 OR 优先级 OR 绑核），改前留复现手段。

## Capability Boundaries + Hand-off

| User Intent | Skill |
|---|---|
| 工程骨架/sdkconfig/构建烧写 | `esp32-idf` |
| 外设驱动与 ISR 引脚层 | `esp32-peripherals` |
| panic 定位、栈溢出现场取证（coredump/JTAG） | `esp32-debug` |
| 低功耗（任务空闲时睡眠策略） | `esp32-lowpower` |
| 上板实测并发时序（逻辑分析仪/压测） | `fw-hil-testing` |

## Workflow 1：并发结构设计

1. 按"事件源 → 处理 → 输出"划任务：一个任务一个职责，避免"上帝任务"。
2. 任务间通信用**队列**传数据副本，不共享裸指针；事件通知优先队列而非全局标志位。
3. 互斥用**互斥量**（考虑优先级继承），计数用**信号量**，单次事件用二值信号量；**不要**用 `vTaskSuspendAll` 当互斥——它只挂起当前核的调度（基线明确）。
4. 周期性非精确调度用**软件定时器**（跑在定时器服务任务上下文）；高精度/硬实时需求改为专用任务+延时原语，勿塞进定时器回调。
5. ISR 上下文只调 `*FromISR` 变体 API（上游 FreeRTOS 通用规则），处理交由任务侧完成。

## Workflow 2：栈与优先级

1. **栈单位是字节**（IDF FreeRTOS 与上游"字"不同，基线高置信）——审代码时先换算：4096 = 4KB，不是 1024 字。
2. 新任务先用保守栈值 + 打印高水位验证，再逐步收紧；不要拍脑袋定"2048 就够"。
3. 优先级：有效范围 0 到 `CONFIG_FREERTOS_MAX_PRIORITIES-1`（默认 25 → 0–24，越大越高，idle=0）；**以本项目 sdkconfig 为准**。
4. 排优先级反转：确认互斥量带优先级继承；同优先级任务确认时间片行为符合预期。
5. 疑似栈溢出的现场取证（backtrace/coredump）移交 `esp32-debug`。

## Workflow 3：双核绑核

1. 读 [smp-pinning](references/smp-pinning.md)：SMP 目标芯片表、每核独立调度器与 idle 任务、portMUX 自旋锁语义。
2. 绑核策略先明确"为什么绑"（cache 局部性/ISR 归属/隔离抖动），再落 `xTaskCreatePinnedToCore()`；不绑核让调度器自由迁移通常是默认起点。
3. 改绑核后实测：不要只看"能跑"，要验证时序与负载分布（无硬件证据标注 `Build Verification Only`）。

## Validation Gates

- `idf.py build` 通过；改动的任务参数与 sdkconfig 一致。
- 长时间运行（至少覆盖最坏业务路径）无任务饿死、无 watchdog 触发。
- 栈高水位在压测后仍有余量；结论有日志/测量证据，无证据不声称"稳定"。

## Pitfalls

1. **不要**按上游 FreeRTOS 的"字"单位计算 IDF 任务栈——**IDF 是字节**，差 4 倍。
2. **不要**假定优先级是 0–31——IDF 默认上限 25（可配），引用必须带"以 sdkconfig 为准"。
3. **不要**用 `vTaskSuspendAll` 当互斥锁——双核下它只挂起当前核，锁不住另一个核。
4. **不要**在 ISR 里调非 FromISR API、做阻塞等待——交给任务侧。
5. **不要**把所有任务都绑到 Core 0——PRO_CPU（Core 0）/APP_CPU（Core 1）分工先读 smp-pinning 再决定。
6. **不要**凭"上游 FreeRTOS 经验"直接断言 IDF 行为——先对照本版本基线与 sdkconfig。

## Official Sources

- [ESP-IDF FreeRTOS (SMP) 文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/freertos_idf.html)
- [FreeRTOS 官网](https://www.freertos.org/)
- [ESP-IDF Releases](https://github.com/espressif/esp-idf/releases)

## Privacy

本 Skill 只分析本地代码与配置，不采集、不外发用户数据或凭据；访问官方链接遵守用户环境网络策略。
