# SMP 与绑核（smp-pinning）

read-when：双核芯片上讨论绑核、核间竞争、portMUX 或调度行为。
基线：IDF FreeRTOS（Vanilla v10.5.1 修改版），走读 2026-09-02，官方 FreeRTOS (SMP) 页（置信度高）。

## 芯片核数表（基线高置信）

| 芯片 | 核数 | SMP | 说明 |
|---|---|---|---|
| ESP32 | 双核 Xtensa LX6 | 是 | Core 0=PRO_CPU / Core 1=APP_CPU |
| ESP32-S2 | 单核 | 恒 unicore | `CONFIG_FREERTOS_UNICORE` |
| ESP32-S3 | 双核 Xtensa LX7 | 是 | Core 0=PRO_CPU / Core 1=APP_CPU |
| ESP32-C3 | 单核 RISC-V | 恒 unicore | `CONFIG_FREERTOS_UNICORE` |
| ESP32-C6 | 单核 RISC-V（另有 LP 核） | 恒 unicore | LP 核不跑 IDF FreeRTOS 主任务模型 |
| ESP32-P4 | 双核 RISC-V | 是 | Core 0=PRO_CPU / Core 1=APP_CPU |
| ESP32-H4 | — | 是（SMP 目标） | 基线 §11 SMP 清单列出；能力细节见 esp32-variants 核验 |

覆盖 Xtensa（ESP32/S3）与 RISC-V（P4）两种架构——SMP 语义跨架构一致，勿按架构分叉记忆。

## IDF FreeRTOS SMP 关键语义（基线高置信）

1. **每核独立调度器与 idle 任务**——"系统空闲"是每核各自的 idle。
2. **核心亲和**：`xTaskCreatePinnedToCore()` 指定任务运行核；未绑核任务可被任一核调度。
3. **栈单位是字节**（与上游"字"不同）。
4. **临界区用 portMUX 自旋锁**——持锁期间本核中断被屏蔽，所以临界区必须极短、绝不阻塞。
5. **`vTaskSuspendAll()` 只挂起当前核的调度器**——双核下不能当互斥用（高频误用点）。
6. Core 0=PRO_CPU / Core 1=APP_CPU 的命名反映"系统核/应用核"分工；绑 Core 0 前先确认系统负载现状（运行时实测，勿凭印象断言某协议栈固定跑哪核）。

## 绑核决策树

```text
为什么绑核？
├── 没有明确理由 → 不绑核（默认），先测基线
├── 隔离抖动（实时任务怕被系统负载拖累）→ 重任务绑 APP_CPU（Core 1）
├── 外设 ISR/驱动归属某核 → 相关任务与 ISR 同核（减少跨核同步）
└── 降低功耗/热（空闲核进入 tickless 等）→ 与 esp32-lowpower 联合设计
```

## 验证方法

1. 改绑核前后各跑一轮长稳压测（覆盖最坏业务路径）。
2. 观察：watchdog 是否触发、关键路径抖动、每核 idle 占用。
3. 结论只认实测数据；无硬件时标注 `Build Verification Only` 或 `Pending HIL`。

## 反幻觉提示

- "某外设驱动固定在 PRO_CPU 运行"之类的断言基线未抓取——以实测与官方文档为准。
- 双核芯片上 `CONFIG_FREERTOS_UNICORE` 可强制单核运行（单核芯片则恒为 unicore）——先 `grep sdkconfig` 再讨论绑核。
