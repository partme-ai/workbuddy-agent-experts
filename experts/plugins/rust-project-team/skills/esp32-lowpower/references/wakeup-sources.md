# Wakeup Sources — 深睡唤醒源速查（按基线原文）

> 依据：firmware-skills 日期化基线 §8（官方 sleep_modes 文档，走读 2026-09-02，不自动更新）。
> 只收基线确认的事实；基线之外的一律标 UNVERIFIED。

## 1. 深睡唤醒源（高置信，共 6 类，可组合）

| # | 唤醒源 | 基线要点 | 选型场景 |
|---|---|---|---|
| 1 | **RTC Timer** | µs 精度定时唤醒 | 周期上报、定时采样（主路径默认） |
| 2 | **Touch** | 触摸传感器唤醒 | 免按键交互面板 |
| 3 | **EXT0** | 单个 RTC GPIO 电平唤醒 | 单按键/单传感器事件 |
| 4 | **EXT1** | 多个 RTC GPIO 组合唤醒；**ANY_LOW 额外支持：S2/S3/C6/H2** | 多按键、多事件源"任一唤醒" |
| 5 | **ULP 协处理器** | 主 CPU 睡死时由 ULP 守夜，满足条件再唤醒主机 | 极低占空比采样（形态见 §2） |
| 6 | **deepsleep GPIO wake** | 基线列举的深睡 GPIO 唤醒手段 | 具体语义以官方文档为准（运行时核验） |

组合提示：多源可叠加（如 timer 兜底 + EXT1 按键即醒）——上报节奏靠 timer，紧急事件靠 GPIO，两不误。

## 2. ULP 形态按芯片（高置信）

| 芯片 | ULP/LP 形态 |
|---|---|
| ESP32 | ULP-FSM |
| ESP32-S2 / S3 | RISC-V ULP **或** FSM 核（官方 get-started 原文） |
| ESP32-C6 / P4 | LP 核（20 / 40 MHz，官方页） |

写 ULP 程序前先确认 target；ULP/LP 编程模型与工具链细节以官方 ULP 文档为准（运行时核验），不在本包展开。

## 3. 配置模式（API 族）

```c
/* 常用 esp_sleep 启用 API 族——签名与枚举以官方 API 文档为准（运行时核验） */
esp_sleep_enable_timer_wakeup(<us>);            /* #1 timer */
esp_sleep_enable_ext0_wakeup(<gpio>, <level>);  /* #3 EXT0：单 RTC GPIO + 电平 */
esp_sleep_enable_ext1_wakeup(<mask>, <mode>);   /* #4 EXT1：多 RTC GPIO 掩码 + 模式 */
/* 可叠加多个唤醒源后统一进入 deep sleep（进入 API 名以官方文档为准） */
```

- 唤醒后用**复位/唤醒原因查询**（esp_sleep / esp_reset 原因族，具体函数名运行时核验官方文档）判断"这次为什么醒"，并打进启动日志。
- GPIO 类只认 **RTC GPIO 集合**；具体引脚以芯片数据手册/官方引脚文档为准——**引脚事实不确定即停**（反幻觉红线）。

## 4. 基线之外 = UNVERIFIED（禁止写入答案）

- UART 唤醒、蓝牙 wake 等基线未列举的唤醒手段：是否支持、支持条件，全部查官方 sleep_modes 页（运行时核验）。
- 每芯片"支持哪些唤醒源"的完整矩阵：查官方文档分芯片页，不凭本表外推。
- 各唤醒源的唤醒时延、功耗增量数值：实测。

## 5. 验收（真机）

1. 逐源触发：每个已配置的唤醒源单独触发一次，日志出现对应唤醒原因。
2. 组合触发：timer 周期醒 + 事件即醒并存，互不吞事件。
3. 未配置的唤醒源不误触发（配置了 EXT1 的板子不该被抖动的非 RTC 引脚唤醒）。
4. 无真机 = `Pending HIL`，路由 `fw-hil-testing`。
