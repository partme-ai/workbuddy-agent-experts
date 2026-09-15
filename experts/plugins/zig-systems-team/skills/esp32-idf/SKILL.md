---
name: esp32-idf
license: Apache-2.0
description: Scaffold, port, configure, build, and flash ESP-IDF projects for the ESP32 family — idf.py workflow (create-project/set-target/menuconfig/build/flash/monitor), sdkconfig decisions, partition tables (factory + dual OTA slots), component-manager dependency locking (idf_component.yml / managed_components / dependencies.lock), v5→v6 migration of removed legacy drivers and esp-mqtt, and build/flash troubleshooting. Use when users mention ESP-IDF, idf.py, sdkconfig/menuconfig, partitions.csv/分区表, CMakeLists.txt, managed_components/依赖锁定, 烧写/monitor, or v5 工程升级 v6 编译报错. Route task/concurrency design to esp32-freertos, pin-level drivers to esp32-peripherals, chip selection to esp32-variants, and OTA, secure boot, Wi-Fi provisioning, low power, and crash debugging to their dedicated esp32-* skills.
---

# ESP-IDF 工程与构建（esp32-idf）

本 Skill 是 ESP32 家族在 ESP-IDF 工具链下的工程入口：建工程、定 target、分区表、依赖锁定、构建烧写与 v5→v6 迁移排障。并发模型与业务代码交给 esp32-freertos，引脚与外设驱动交给 esp32-peripherals。

## Determine Task Type

先判定交付物，再进对应 Workflow：

1. **新建工程** — 从零搭 IDF 工程骨架并跑通 build→flash→monitor → 走 Workflow A。
2. **移植既有工程**（重点：v5 → v6 跨大版本）— 编译报错、legacy 驱动被移除、esp-mqtt 转组件管理器 → 走 Workflow B，并读 [v5-to-v6-migration](references/v5-to-v6-migration.md)。
3. **组件开发 / 依赖管理** — 添加第三方组件、锁定版本、修复 dependencies.lock → 走 Workflow C。
4. **OTA 改造**（双 app 槽 + otadata + 回滚）→ **本 Skill 只建分区表骨架，实施移交 `esp32-ota`**。
5. **芯片还没选** → 先移交 `esp32-variants`。

## Preflight（先运行时核验，再动手）

```bash
idf.py --version          # 本机 IDF 实际版本；不在 PATH 会直接报错
# 已有工程时：
ls CMakeLists.txt sdkconfig partitions.csv dependencies.lock 2>/dev/null
grep -m1 "CONFIG_IDF_TARGET" sdkconfig 2>/dev/null   # 项目当前 target
ls managed_components 2>/dev/null
```

区分**三个版本轴**（不要混用）：

| 版本轴 | 怎么确认 | 决定什么 |
|---|---|---|
| 本机 IDF | `idf.py --version` 实测 | 当前机器能编什么 |
| 项目锁定 | 工程实际检出的 esp-idf tag/分支（`$IDF_PATH`）+ `dependencies.lock` 锁定的组件版本 | 项目真实行为；`managed_components/` 勿手改 |
| 官方 latest stable | 基线为 **v6.1**（截至 2026-09-02，运行时核验 GitHub releases） | 升级评估参考，不自动采用 |

- **target 必须与芯片实物核对**：模组丝印/原理图上的芯片型号，与 `set-target` 的值一致才能继续；对不上就停下来问。
- v6.1、v6.0.2、v5.5.5 等具体版本号均为"截至 2026-09-02"的基线值，引用时必须带日期并提示运行时核验。

## Offline Baseline

- 本 Skill 的 ESP-IDF 事实以日期化基线为准：**ESP-IDF v6.1**，走读 **2026-09-02**，不自动更新。
- v6.x 相对 v5.x 有破坏性变更（旧版驱动移除、esp-mqtt 转组件管理器）；示例避免依赖已移除的 legacy API。
- 之后的版本行为变化，以官方文档与 GitHub releases 为准，不凭记忆断言。

## Contracts（硬件契约）

- **芯片/模组型号**：以实物丝印或原理图为准，禁止凭工程名猜 target。
- **Flash 大小与分区偏移**：menuconfig 的 flash 容量必须与实物一致；分区偏移不确定时**禁止编造**，用自动排布（见 [partition-table-template](references/partition-table-template.md)）。
- **烧写通道**：确认串口设备（`-p PORT` 或 `ESPPORT`）与权限；烧写会改写设备状态。
- 分区表、引脚、内存布局类问题：不确定即停，路由运行时核验或官方源。

## Capability Boundaries + Hand-off

本 Skill 覆盖工程骨架/构建/依赖/迁移排障。以下意图显式移交：

| User Intent | Skill |
|---|---|
| 任务/队列/信号量/双核 pinning | `esp32-freertos` |
| GPIO/I2C/SPI/UART/ADC/PWM 引脚与驱动 | `esp32-peripherals` |
| 还没定芯片 / 换芯片评估 | `esp32-variants` |
| OTA 升级实施（esp_ota_* / https ota / 回滚确认） | `esp32-ota` |
| Secure Boot v2 / Flash 加密 | `esp32-secureboot` |
| Wi-Fi 配网（Unified Provisioning/SoftAP/BLE） | `esp32-wifi-provision` |
| Deep/Light sleep、续航设计 | `esp32-lowpower` |
| panic/coredump/JTAG 解读 | `esp32-debug` |
| 上板验收测试（声称"硬件可用"之前） | `fw-hil-testing` |
| 无板先跑逻辑（QEMU/Wokwi） | `fw-emulation` |
| Rust no_std 的 ESP32（esp-hal） | 包外 `rust-skills/rust-embedded`（refuse 并移交） |

## Workflow A：新建工程

```bash
idf.py create-project hello_idf && cd hello_idf
idf.py set-target esp32s3        # 清空 build/ 并重新生成 sdkconfig；默认 target 是 esp32
idf.py menuconfig                # 决策点见 references/menuconfig-decisions.md
idf.py build                     # 期望：build/ 下生成 .bin/.elf/.map，末尾报告分区占用
idf.py -p /dev/ttyUSB0 flash monitor   # 可链式执行，顺序由 idf.py 保证；-p 也可用 ESPPORT
```

期望输出：esptool 写入完成后芯片复位并输出 boot log；monitor 持续打印运行日志（按其提示的快捷键退出）。

- 分区需求超"单 factory"时，先改 `partitions.csv` 再 build（模板见 references）。
- 加第三方组件：`idf.py add-dependency <ns/name=版本>` 写入 `idf_component.yml`；依赖递归解析后落在 `managed_components/`，并生成 `dependencies.lock`（损坏可用 `idf.py reconfigure` 重建）。

## Workflow B：v5 → v6 迁移排障

1. `idf.py --version` 确认本机 IDF 大版本，与项目锁定版本对照。
2. 按报错定位：头文件/符号缺失 → 疑似 legacy 驱动移除；mqtt 相关 → 疑似转组件管理器。
3. 读 [v5-to-v6-migration](references/v5-to-v6-migration.md) 的破坏性清单与核验方法；**禁止**凭记忆背"被移除 API 的完整清单"。
4. 逐条改用新式接口后重新 build；每修一类错误单独提交，便于回退。

## Workflow C：组件与版本锁定

1. `idf.py add-dependency espressif/mqtt` 之类声明进 `idf_component.yml`。
2. 核对 `dependencies.lock` 与 `managed_components/` 一致；两者都纳入版本控制。
3. 不要手改 `managed_components/` 内容——升级走依赖声明。
4. CI 可复现构建 = 固定 esp-idf 检出版本 + 提交 `dependencies.lock`。

## Validation Gates

- `idf.py build` 零 error，产物分区占用不超过目标 app 分区（构建时会校验镜像放得进某个 app 分区）。
- `idf.py partition-table` 打印结果与 `partitions.csv` 预期一致。
- flash 前复述 target 与串口；monitor 看到 boot log 且无反复复位。
- 无真实硬件证据时，汇报必须标注 `Build Verification Only`。

## Pitfalls

1. **不要**跳过 `set-target` 直接拿别的芯片的 build 目录烧写——set-target 会清 build 并重生成 sdkconfig，混用会烧错镜像。
2. **不要**手改 `managed_components/` 里的代码来"修 bug"——升级即丢，改上游或加补丁组件。
3. **不要**编造分区偏移值——Offset 留空让工具自动排布，app 分区天然 64KB 对齐。
4. **不要**在 v6.x 里继续用 v5 的 legacy 驱动调用或假设 esp-mqtt 内置——先读迁移参考。
5. **不要**把"build 通过"汇报成"板子可用"——烧写验证前只算 Build Verification Only。
6. **不要**引用无日期的版本号——所有"最新版本"必须带"截至 2026-09-02"并提示运行时核验。

## Official Sources

- [idf.py 命令指南](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/tools/idf-py.html)
- [分区表](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/partition-tables.html)
- [组件管理器](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/tools/idf-component-manager.html)
- [ESP-IDF Releases](https://github.com/espressif/esp-idf/releases)
- [VS Code ESP-IDF 扩展](https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/index.html)

## Privacy

本 Skill 不采集、不存储、不外发用户数据、Wi-Fi 凭据或密钥。烧写与 monitor 只访问用户明确指定的本地串口设备；访问官方链接遵守用户环境网络策略。
