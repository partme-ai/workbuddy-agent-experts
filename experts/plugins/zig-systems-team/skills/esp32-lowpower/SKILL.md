---
name: esp32-lowpower
license: Apache-2.0
description: Design and troubleshoot ESP32 low-power sleep strategies on ESP-IDF — light-sleep vs deep-sleep selection, the six deep-sleep wakeup sources documented in the dated baseline (RTC timer with µs precision, touch, EXT0 single RTC GPIO, EXT1 multi RTC GPIO with ANY_LOW on S2/S3/C6/H2, ULP coprocessor, deep-sleep wake GPIO), ULP distribution across the family (ESP32=ULP-FSM, S2/S3=RISC-V ULP or FSM, C6/P4=LP core), RTC-memory retention vs NVS snapshot trade-off, and a power-meter current acceptance method. Use when users mention 低功耗, deep sleep/深睡, light sleep, 电池续航/月级续航, 唤醒源, ULP, or ask to quote deep-sleep current in µA. Refuses to write specific deep-sleep µA numbers from memory — those are UNVERIFIED in the baseline and must be measured with a power meter on real hardware (route fw-hil-testing). Do NOT use for FreeRTOS task/tick design (route esp32-freertos), chip selection (route esp32-variants), or project scaffolding/partitions (route esp32-idf).
---

# ESP32 低功耗（睡眠策略与唤醒源）

睡眠策略由**业务节奏**决定（多久醒一次、醒着干什么、什么事件必须立刻醒），不由"某个 µA 数字"决定。本 Skill 给出基线（高置信）的双模式与唤醒源事实；**深睡电流具体数值在基线中是 UNVERIFIED——一律拒绝背数字，给实测方法**。

## Determine Task Type

1. **电池设备续航设计**（周期上报/月级续航）→ Workflow A（决策表主路径）。
2. **唤醒源选型与配置**（按键/定时/触摸/ULP）→ Workflow B，读 [wakeup-sources](references/wakeup-sources.md)。
3. **睡眠电流疑问 / 续航测算** → Workflow C（实测验收，含对"背 datasheet 数字"的 refusal 立场）。
4. **跨睡眠保存数据** → RTC 内存保留 vs NVS 快照取舍（见 Contracts 后专节）。

## Prerequisites / Preflight

```bash
idf.py --version                                          # 本机 IDF 实际版本
grep -E "CONFIG_ESP_SLEEP|CONFIG_PM_" sdkconfig 2>/dev/null | head -10   # 现有睡眠/电源管理配置
grep -m1 "CONFIG_IDF_TARGET" sdkconfig 2>/dev/null        # 目标芯片——决定唤醒源集合与 ULP 类型
```

1. **读 target 先行**：芯片型号决定唤醒源集合与 ULP 形态（见 Contracts 第 3 条）；没有芯片实物/工程 target 前，不回答"哪些唤醒源可用"。
2. 确认供电形态：电池化学体系与稳压器静态电流属于**板级事实**，问用户/原理图，不猜。
3. 真机与功率计（USB 功率计或源表）——电流验收必备，没有就在结论里标 Pending HIL。

## Offline Baseline

- ESP-IDF 基线 = **v6.1**（走读 **2026-09-02**，不自动更新）。低功耗事实引自日期化基线 §8（官方 sleep_modes 文档，置信度高）。
- **µA 具体数值置信度为中**（数据手册搜索转述，未直接抓取 PDF）——引用任何具体电流数字前必须运行时核验或实测；本 Skill 一律不给数字。
- 之后的版本行为变化以官方 sleep_modes 文档为准，不凭记忆断言。

## Contracts（设备契约）

1. **双模式定义（高置信）**：**Light-sleep** = 时钟门控、状态保持、无线断电；**Deep-sleep** = CPU/大部分 RAM/数字外设断电，仅 RTC 控制器、ULP、RTC FAST/SLOW 内存供电。
2. **深睡唤醒源（高置信，基线原文列举）**：RTC Timer（µs 精度）、Touch、EXT0（单 RTC GPIO）、EXT1（多 RTC GPIO，S2/S3/C6/H2 额外支持 ANY_LOW）、**ULP 协处理器**、deepsleep GPIO wake；**可组合**。基线未收录的唤醒手段（如 UART/蓝牙 wake）一律标 UNVERIFIED，不得写入答案。
3. **ULP 分布（高置信）**：ESP32 = ULP-FSM；S2/S3 = RISC-V ULP **或** FSM 核；C6/P4 = LP 核（20/40 MHz）。写 ULP 程序前先确认 target 的 ULP 形态。
4. **深睡电流数值 = UNVERIFIED**：基线仅确认"µA 数量级"（官方页只给 SPI Flash 待机 <30µA / Deep Power-Down <1µA）；"典型 10µA / ULP 运行 ~150µA"出自数据手册转述。**本 Skill 不把任何具体数值当事实输出**——验收只认板级实测（Workflow C）。
5. **睡眠是状态破坏性操作**：deep sleep 杀掉普通 RAM（任务栈、连接状态不保留），light sleep 断无线。进入前必须先安顿状态（见下节）。

## RTC 内存保留 vs NVS 快照（取舍决策）

| 判据 | RTC 内存保留 | 醒后/睡前快照到 NVS |
|---|---|---|
| 跨"换电池/掉电"存活 | **否**（deep sleep 仍靠电池供电 RTC 域） | **是**（flash 持久） |
| 访问速度 | 醒来即得，最快 | 需读回（NVS API） |
| 容量 | 小（RTC 慢速内存，大小以芯片规格为准——运行时核验） | 大（按 flash 预算） |
| 写入代价 | 无 flash 磨损 | 有写入寿命考量，别在高频循环里刷 |
| 适用 | 睡眠计数器、上次上报时间戳等小状态 | 配置、累计量、必须掉电不丢的数据 |

常见组合：小状态放 RTC 内存做**睡眠间**续命；同时把"掉了电池也不能丢"的结论**在进入 deep sleep 前**写一次 NVS。RTC 内存变量的声明方式（常用 `RTC_DATA_ATTR` 一族）以官方深度睡眠文档为准（运行时核验）。

## Capability Boundaries + Hand-off

不做：FreeRTOS 任务/tick-less 层面的功耗设计、芯片选型、工程骨架、以及**任何具体电流数值的承诺**。

| User Intent | Skill |
|---|---|
| 工程/分区/sdkconfig 基础 | `esp32-idf` |
| 任务挂起/队列与睡眠的配合（tick 层） | `esp32-freertos` |
| 还没定芯片 / 换低功耗芯片评估 | `esp32-variants` |
| 功耗实测/真机在环验收（功率计、长跑） | `fw-hil-testing` |
| ULP 之外的"无板先验证业务逻辑" | `fw-emulation` |
| 蓝牙/Wi-Fi 配网在睡眠场景的取舍 | `esp32-wifi-provision` |

## Workflow A — 电池设备月级续航的睡眠策略（主路径）

按决策表落策略，每一步都要能回答"为什么不是另一格"：

1. **问业务节奏**：多久上报一次？有没有必须立刻响应的外部事件？答不出就先问，不要默认。
2. **对决策表**：

| 需求 | 策略 |
|---|---|
| 周期上报（分钟~小时级占空比） | **deep sleep + RTC timer 唤醒**（µs 精度定时，醒→采样→上报→再睡） |
| 按键/外部事件必须秒级唤醒 | **deep sleep + EXT0（单 RTC GPIO）/ EXT1（多 RTC GPIO）**，注意 RTC GPIO 引脚集合限制 |
| 毫秒级恢复、可接受保连接代价 | **light sleep**——但无线断电是基线明示，"低功耗又不断网"不成立 |
| 采样比唤醒整机更省 | 交 **ULP/LP 核**（形态按 target 查 Contracts 第 3 条） |

3. **安顿状态**：入睡小状态 → RTC 内存；掉电不可丢 → 入睡前写 NVS。
4. **配置唤醒源**：见 Workflow B。
5. **电流验收**：见 Workflow C；没有实测值之前，续航结论一律不出口。

## Workflow B — 配置唤醒源

1. 读 target 与 [wakeup-sources](references/wakeup-sources.md)，确认所选唤醒源在该芯片上存在（基线只保证 6 类的存在与 EXT1 ANY_LOW 的芯片范围；逐芯片完整支持矩阵以官方文档为准——运行时核验）。
2. 用 esp_sleep 启用 API 族声明唤醒源（如 `esp_sleep_enable_timer_wakeup()` / `esp_sleep_enable_ext0_wakeup()` / `esp_sleep_enable_ext1_wakeup()` 一族——具体签名与枚举以官方 API 文档为准，运行时核验），多个唤醒源可叠加，最后进 deep sleep。
3. 唤醒后用**复位原因/唤醒原因查询**记录"这次为什么醒"，写进启动日志——没有唤醒原因日志的睡眠代码不算完成。
4. GPIO 类唤醒源只认 **RTC GPIO** 集合：具体哪些引脚可用，以芯片数据手册/官方引脚文档为准，**不确定即停**（反幻觉红线：引脚/复用不凭记忆）。

## Workflow C — 睡眠电流实测验收（含 refusal 立场）

**Refusal 立场**：用户问"deep sleep 是 10µA 对吧"——回答不是"对"，是**拒绝把这个数字当事实**：它出自数据手册转述（基线标注运行时核验），且数据手册值是芯片裸电流，**不是你这块板的电流**（外设漏电、上拉电阻、LED、稳压器静态电流都会数倍放大）。正确动作：

1. 搭测量：功率计/源表串联进供电回路，记录供电电压与供电方式。
2. 测静态基线：板上所有外设按产品真实配置连接（不要"拆干净再测"）。
3. 让设备进入目标睡眠模式，稳定 ≥5 分钟后记录**平均电流**（闪断式瞬时值不作数）。
4. 用实测值做续航积分估算：`续航 ≈ 电池可用容量 ÷ (占空比加权平均电流)`；估算结果标注输入假设。
5. 长跑与温度维度验收 → `fw-hil-testing`；无真机时结论标 `Pending HIL`。

## Validation Gates

1. 构建级：`idf.py build` 通过，sdkconfig 睡眠相关选项与 target 匹配（Preflight 输出留档）。
2. 功能级（真机）：timer 唤醒按设定周期醒来，启动日志有唤醒原因；GPIO 唤醒触发即醒；每个配置的唤醒源逐一实测触发。无真机 = **Pending HIL**。
3. 电流级（必须）：按 Workflow C 拿到板级实测值并留档（供电方式、板级配置、平均电流）；数据手册数字不作为验收依据。
4. 续航结论必须给出实测输入与估算公式，缺实测输入的续航承诺不出口。

## Pitfalls

1. **不要**把"典型 10µA / ULP ~150µA"这类转述数字写进答案或按它算续航——UNVERIFIED，只认板级实测。
2. **不要**假设所有唤醒源在所有芯片上都存在——EXT1 的 ANY_LOW 仅 S2/S3/C6/H2（基线）；逐芯片矩阵运行时核验。
3. **不要**把跨睡眠状态留在普通 RAM 里——deep sleep 只保 RTC 域；掉电不丢的数据必须进 NVS。
4. **不要**把 light sleep 讲成"低功耗且不断网"——无线断电是基线明示行为。
5. **不要**用 GPIO 类唤醒却随便挑引脚——只认 RTC GPIO 集合，引脚事实不确定即停。
6. **不要**在无实测数据的情况下向用户承诺"能撑 X 个月"——续航承诺必须有实测电流输入。

## Official Sources

- [ESP-IDF Sleep Modes](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/sleep_modes.html)
- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/)
- [Espressif ESP32 产品页（ULP/LP 核分布）](https://www.espressif.com/en/products/socs)

## Privacy

本 Skill 不采集、不外发用户数据；功耗实测记录（供电方式、板级配置、电流值）仅在本地留存，随报告外发前应去掉设备序列号等标识信息；访问官方链接遵守用户环境网络策略。
