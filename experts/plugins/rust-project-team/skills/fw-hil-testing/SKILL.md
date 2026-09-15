---
name: fw-hil-testing
license: Apache-2.0
description: "Run hardware-in-the-loop (HIL) acceptance as the evidence-chain hub of this pack — instantiate an Evidence Contract matrix (验收项/前置条件/操作/观察手段/预期/证据形式 covering 上电启动, 核心功能, 异常路径 断电/断网/异常输入, 长时间运行, 升级路径), enforce Pre-Flash checks (serial probe ready, bootloader/校准区/NVS untouched, rollback image saved first), grade completion badges Build Verification Only → Boot Verified (QEMU) → HIL Verified with no overclaiming, route failures (build broken → fw-emulation, OpenWrt brick → openwrt-serial-recovery, ESP32 crash → esp32-debug), and map single-unit evidence to staged commercial gates. Use when the user asks 固件怎么算可以发货 / 真机验收 / HIL 测试 / 硬件验收 / 断电测试 / 老化测试 / 升级回滚验收, reports 烧录后串口无输出 or 真机上功能不对, or claims QEMU 里跑通了可以直接发货 (refuse: boot-verified is not HIL-verified). Items marked Pending HIL by other skills converge here; packaging, checksums and release go to fw-release-gate."
---

# 固件 HIL 在环验收（证据链中枢）

本 Skill 是 firmware-skills 包的**证据链中枢**：其他技能挂起的 `Pending HIL` 项、以及"固件写完了怎么算可以发货"的判定，都在这里落成证据。核心背语：**构建成功 ≠ 硬件可用**——没有真机证据，就没有"可用"二字。

## Determine Task Type

1. **OpenWrt 网关 HIL**：目标设备是 OpenWrt 网关/盒子（N1/Amlogic、x86 软路由、mt7981 类）→ Workflow A（网关型矩阵）。
2. **ESP32 MCU HIL**：目标是 ESP32 片上固件 → Workflow B（MCU 型矩阵）。
3. **HIL 失败排障**：烧录失败、烧完无输出、真机上行为不符 → Workflow C（失败三分类路由）。
4. **发货判定 / 证据评审**：已有部分证据，问"能不能发"→ 按徽章评级（[completion-badges](references/completion-badges.md)），缺行先补行再评级。

## Prerequisites / Preflight

运行时核验先行：

```bash
# ESP32：工具链与串口设备
idf.py --version 2>/dev/null || echo "IDF not in PATH"
ls /dev/tty.usb* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "no serial device listed"
# OpenWrt 网关：构建产物是否在手
ls -l bin/targets/*/ 2>/dev/null || echo "no image-builder output"
```

Pre-Flash Checks（烧录前逐条过，任何一条不满足先停下来）：

1. **串口探测就绪**：能列出目标串口设备并按 `115200 8N1`（常见值，以板实测为准）打开；无法观察串口的设备，至少明确一条替代观察通道（HDMI、LED、网络可达性）。
2. **分区红线**：明确本次烧录写哪些分区；**bootloader / 出厂校准 / NVS 默认不碰**。分区事实以运行时核验为准（ESP32：`idf.py partition-table`；盒子：以设备文档与 ophub 工具矩阵为准），不确定即停。
3. **可回退固件必须先留存**：烧录前留存当前可用固件——OpenWrt 盒子走 ddbr 备份（→ `openwrt-serial-recovery`）；ESP32 留存"已知良好"完整镜像 + sha256。回退方案要能回答：文件在哪、校验和是多少、怎么刷回去。
4. **破坏性确认**：向用户复述目标设备与将擦写的分区，获确认后再执行。

## Offline Baseline

- 走读日期 **2026-09-02**，不自动更新。
- OpenWrt 基线 **25.12.5**；ophub 上游 HEAD **`c593d56`**；ESP-IDF 基线以 Phase 2 基线文档为准（当时 **v6.1**）。
- HIL 方法本身不绑定版本；引用的命令（idf.py flash/monitor、IB `make image`、ddbr）以上述基线为准，其后行为变化以官方源为准。

## Contracts（硬件契约）

动手前记录在案，缺项先问，不猜（参照 rust-embedded 的 Mandatory Hardware Contracts 模式）：

- 确切设备型号/板版本、供电方式、串口参数（以板实测）；
- 烧录工具与端口、本次将写入的分区清单（红线区除外）；
- 观察通道：串口日志 / SSH / Web 界面 / LED / 万用表·功率计（异常路径与功耗采样需要）；
- 回退固件的位置与校验和（Pre-Flash 第 3 条的落档）；
- 反幻觉红线：引脚、分区偏移、DTB 文件名、内存布局——不确定禁止编造，标 `Pending HIL` 转运行时核验。

## Evidence Contract（验收矩阵）

一切"已验证/可发货"的断言必须挂在**验收矩阵**上：每行 = 一个验收项，六列齐全（模板、实例行集见 [evidence-matrix](references/evidence-matrix.md)）：

| 列 | 要求 |
|---|---|
| 验收项 | 一句可判定的陈述（"拔电 10 次后均自动恢复服务"） |
| 前置条件 | 执行该行前必须成立的事（已刷 X 版本、已留存回退镜像） |
| 操作 | 确定性动作（怎么断电、断多久、发什么异常输入） |
| 观察手段 | 用什么看结果（串口日志 / SSH 命令 / Web / 测量仪表） |
| 预期 | 可判定的通过线 |
| 证据形式 | 截图 \| 日志 \| 测量值——至少其一，落文件 |

必选覆盖五类行，缺一类不算矩阵完整：

1. **上电启动**：冷启动到可用的时长与状态；
2. **核心功能**：该设备存在的理由，逐条成行；
3. **异常路径**：断电 / 断网 / 异常输入——最容易漏、返工最贵；
4. **长时间运行**：soak 采样 ≥24h 起步（内存、温度、服务存活、重启计数）；
5. **升级路径**：升级成功 + 升级中断/回滚（机制侧 → `esp32-ota`）。

证据纪律：每份证据带**设备标识 + 固件版本 + 日期**，能与矩阵行对上；禁止补拍、代拍、跨设备挪用证据。

## 分级完成标准（徽章）

三级徽章语义，**禁止越级声明**（定义、越级话术对照与自查见 [completion-badges](references/completion-badges.md)）：

| 徽章 | 取得条件 | 允许的声明上限 |
|---|---|---|
| `Build Verification Only` | 仅构建通过 | "编译产出镜像，未运行验证" |
| `Boot Verified (QEMU)` | 无板环境可引导 + 冒烟（→ `fw-emulation`） | "QEMU 内可启动、冒烟通过" |
| `HIL Verified` | 验收矩阵全行真机证据齐 | "真机矩阵全行通过，证据可查" |

没拿到哪级就只能声明到哪级；遗留标记 `Pending HIL` 继续作为**单行级**标记使用（该行尚未取得真机证据），徽章是**交付物级**状态，两者配合使用。

## Capability Boundaries + Hand-off

本 Skill 只做验收与证据，不做构建、不做机制实现、不在无仪器时下硬件设计定论：

| User Intent | Skill |
|---|---|
| 构建 / 重打包镜像 | `openwrt-image-build` / `openwrt-amlogic-remake` |
| 没硬件、先在无板环境跑通 | `fw-emulation` |
| OTA / 回滚机制实现 | `esp32-ota` |
| 烧录失败已致不可启动（OpenWrt 侧） | `openwrt-serial-recovery` |
| ESP32 崩溃 / 复位定位 | `esp32-debug` |
| 证据齐 → 发布与命名校验 | `fw-release-gate` |
| 任务分型入口 | `fw-core` |

失败三分类路由（细则走 Workflow C）：

| 失败类别 | 特征 | 路由 |
|---|---|---|
| 构建失败 | 镜像没产出或起不来，疑似产物问题 | `fw-emulation` 无板复现，分离"镜像坏"vs"板问题"；纯构建报错回 `fw-toolchain` / `esp32-idf` / `openwrt-image-build` |
| 烧录失败 | 烧写报错、烧完不可启动（OpenWrt 侧） | `openwrt-serial-recovery`（先软后硬梯度） |
| 功能失败 | 烧进去了但崩溃/复位/行为不符 | `esp32-debug`（ESP32）；OpenWrt 运行期先 `logread` / `dmesg` triage |

**商业门禁模式**（矩阵如何映射到批量放行；模式提炼自 TinyNAS 闭环实践，映射表见 [evidence-matrix](references/evidence-matrix.md) §4）：单台矩阵全绿只是 G1 工程样机级门票；批量发货按 **G1 工程样机连续运行 → G2 单渠道小批量受控观察（激活率/启动率/退款率类指标）→ G3 多渠道扩量对比 → G4 售后指标门禁**逐级放行，禁止从"单台 HIL Verified"直接跳批量。

## Workflow A — OpenWrt 网关 HIL

1. 记录硬件契约，过 Pre-Flash Checks（ddbr / 镜像备份先行）。
2. 从 [evidence-matrix](references/evidence-matrix.md) §2 实例化网关型矩阵：上电到可用、存储挂载、核心服务、Web 后台、断电恢复循环、断网降级、soak、升级/回退。
3. 刷入目标版本，逐行执行并取证（串口日志 + SSH 命令输出 + Web 截图落文件）。
4. 异常路径必须真做：断电用定时插座或拔电做 N 次循环；断网拔 WAN 看 LAN 侧服务存活；异常输入喂满盘、畸形配置。
5. 全绿 → 打 `HIL Verified` 徽章并归档证据包；有缺行 → 徽章降到实际等级，缺行路由对应技能后复验。

## Workflow B — ESP32 MCU HIL

1. 记录硬件契约，过 Pre-Flash（留存已知良好镜像 + sha256）。
2. 从 [evidence-matrix](references/evidence-matrix.md) §3 实例化 MCU 型矩阵：上电日志与复位原因、外设就绪、配网成败与重试、OTA 升级 + 断电回滚、低功耗实测（若宣称低功耗，µA 级数值以实测为准，不抄数据手册口头值）、soak。
3. `idf.py -p <PORT> flash monitor` 刷入并观察；升级中断电、配网失败重试等异常行必须执行。
4. 崩溃/复位类失败不在本 Skill 定性 → 路由 `esp32-debug`；定性修复后回矩阵复验该行。

## Workflow C — HIL 失败排障（含"烧录后串口无输出"）

1. **先定类再动手**（构建/烧录/功能三分类），不在硬件上反复盲刷。
2. "串口无输出"排查顺序：
   - 观察链路：波特率（115200 常见值，以板实测）、TX/RX 交叉、共地、供电、端口选对没；
   - 烧录证据：烧录日志显示写入成功？写到了对的分区/介质？
   - 最小引导：换已知良好镜像（回退固件）验证"板能响"——能响则属镜像问题（→ 构建失败路由），不响则升级为板/烧录问题；
   - OpenWrt 盒子完全无响应 → `openwrt-serial-recovery`；有输出但崩溃 → `esp32-debug`。
3. 排障期间**不擦红线分区**；每次重烧前确认回退镜像仍在、校验和未变。

## Validation Gates

- 矩阵完整性：五类必选行齐全；每行有证据文件或明确 N/A 理由；不存在"未执行但已勾选"。
- 徽章一致性：声明的徽章与证据一一对应；无真机证据处不得出现 `HIL Verified`。
- 回退演练：至少成功执行一次从留存镜像恢复；未演练的明确标注并列入已知风险。
- 失败闭环：每个失败行已按三分类路由、有结论（修复 / 降级 / 挂牌 Pending HIL）。

## Pitfalls

1. **不要**把 `Boot Verified (QEMU)` 说成"已验证可发货"——QEMU 没有真实电气、存储介质、断电与无线环境，徽章不可越级。
2. **不要**在未留存回退固件前擦写 bootloader/校准/NVS——第一次烧录就要想好怎么退回来。
3. **不要**用"应该没问题"代替矩阵行——每行要么有证据，要么写 N/A 理由。
4. **不要**跳过异常路径（断电/断网/异常输入）直接宣称生产就绪——这是返工与退货的头号来源。
5. **不要**伪造或事后补拍证据——日期、设备标识、版本对不上的证据按无效处理。
6. **不要**把单台样机结论外推成"批量没问题"——批量决策走商业门禁模式逐级放行。
7. **不要**在本 Skill 里下"这是电源/硬件设计缺陷"的定论——硬件嫌疑也要测量定论，无仪器不断言。

## Official Sources

- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/)
- [idf.py 工具](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/tools/idf-py.html)
- [ESP-IDF OTA](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/ota.html)
- [OpenWrt Image Builder](https://openwrt.org/docs/guide-developer/imagebuilder)
- [OpenWrt 串口控制台](https://openwrt.org/docs/techref/hardware/port.serial)
- [ophub amlogic-s9xxx-openwrt](https://github.com/ophub/amlogic-s9xxx-openwrt)

## Privacy

HIL 证据（串口日志、截图、测量记录）可能含设备标识、MAC、网络凭据与用户数据：归档前脱敏，外发前经用户确认；本 Skill 不采集、不存储、不外发任何设备数据；回退镜像按用户数据对待，建议加密存放。
