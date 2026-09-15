---
name: fw-core
license: Apache-2.0
description: Route any embedded-firmware task to the right specialized skill in this pack — OpenWrt Linux gateway firmware (image build, Amlogic box remake, procd init, uci-defaults, storage mount, serial recovery) and ESP32 MCU firmware (ESP-IDF, FreeRTOS, peripherals, Wi-Fi provisioning, OTA, low power, secure boot, debugging, variant selection), plus cross-cutting toolchain, emulation, HIL testing, and release gating. Use when the user mentions 刷机, OpenWrt 镜像/FILES, N1/Amlogic 盒子写 eMMC, 开机自启, 首启配置/UCI, 硬盘挂载, 变砖救援, ESP-IDF 工程/分区表, FreeRTOS 任务, 引脚外设, 配网, OTA 升级, 低功耗, 安全启动, coredump/JTAG, 芯片选型, 交叉工具链, 无板模拟, 硬件验收, or 固件发布命名/校验和. Do NOT use for Rust no_std firmware — hand off to rust-skills/rust-embedded instead.
---

# 固件任务总路由（fw-core）

本 Skill 是 firmware-skills 包的**入口路由**：先分型任务，再交给包内专职 Skill 或显式移交包外 Skill。本 Skill 不直接产出镜像或固件代码。

## Determine Task Type

先判定交付物类型，再路由：

1. **Linux 网关固件（OpenWrt 系）** — 目标是可刷写的 OpenWrt 镜像或其 rootfs 内容 → OpenWrt 链路（见 [routing-openwrt](references/routing-openwrt.md)）。
2. **MCU 固件（ESP-IDF 系）** — 目标是 ESP32/ESP32-S/C 系列片上固件 → ESP32 链路（见 [routing-esp32](references/routing-esp32.md)）。
3. **Rust no_std 固件** — 用户要求用 Rust 写 no_std/embedded-hal/Embassy/RTIC 固件 → **本包不覆盖**，显式移交 `rust-skills/rust-embedded`（见 Hand-off 表最后一行：refuse 并路由）。
4. **仅要"能跑"的模拟验证** — 没有硬件、只想先在 QEMU/仿真里跑通 → `fw-emulation`。

分型判据细节（按关键词还是按交付物、拿不准时问什么）见 [task-typing](references/task-typing.md)。

## Prerequisites / Preflight

路由前必须先确认两件事，用户没说就问，**不要猜**：

1. **目标平台**：哪个设备/芯片？（如 "N1 盒子"、"x86 软路由"、"ESP32-S3"、"mt7981 路由器"）
2. **交付物类型**：完整镜像、rootfs 改造、运行时配置、还是一段应用代码？

运行时核验（进入具体 Skill 后仍须重验）：

```bash
# 构建 OpenWrt 镜像需 Linux x86_64（或 Docker 内 Linux）
uname -m && make --version | head -1
# ESP-IDF 工程需确认 IDF 版本
idf.py --version 2>/dev/null || echo "IDF not in PATH"
```

**背语（每次路由前默念）："构建成功 ≠ 硬件可用。"** 镜像编出来只代表 Build Verification；无真实硬件证据不得声称"已在设备上验证"（CONVENTIONS §5）。

## Offline Baseline

- OpenWrt 基线 = **25.12.5**（上游走读日期 2026-09-02，不自动更新）。
- ophub（amlogic-s9xxx-openwrt）基线 = 上游 HEAD `c593d56`。
- ESP-IDF 基线以 Phase 2 基线文档为准（esp32-idf 内声明）。
- 上述版本之后的行为变化，以官方源为准，不凭记忆断言。

## Contracts（设备契约）

- **PROFILE 与目标设备必须实证**：OpenWrt 的 `PROFILE` 名以 `make info` 输出为准；设备型号以用户提供的实物型号/bootlog 为准。两者对不上就停下来问，**不确定禁止编造**。
- 涉及 DTB 文件名、引脚复用、分区偏移、内存布局、寄存器的问题：**不确定即停**，路由到运行时核验（fw-hil-testing / openwrt-serial-recovery）或官方源，禁止凭记忆给值（CONVENTIONS §2 反幻觉红线）。
- 写 eMMC/烧写 flash 是破坏性操作：执行前必须复述目标盘符并获用户确认。

## Capability Boundaries + Hand-off 路由表

本 Skill 只做分型与路由。下表覆盖本包全部 19 个专职 Skill 与 1 个包外移交：

| User Intent | Skill |
|---|---|
| 构建 OpenWrt 镜像 / FILES 覆盖注入 | `openwrt-image-build` |
| N1 / Amlogic 盒子 / 写 eMMC（重打包） | `openwrt-amlogic-remake` |
| 开机自启 / init 脚本（procd） | `openwrt-procd-init` |
| 首启配置 / UCI / uHTTPd / 防火墙 | `openwrt-uci-defaults` |
| 硬盘挂载 / USB 存储 | `openwrt-storage-mount` |
| 变砖 / 串口救援 | `openwrt-serial-recovery` |
| ESP-IDF 工程结构 / 分区表 | `esp32-idf` |
| FreeRTOS 任务 / 队列 / 同步 | `esp32-freertos` |
| 外设 / 引脚（GPIO/I2C/SPI/UART/PWM/ADC） | `esp32-peripherals` |
| 配网（SmartConfig/BluFi/AP 配网） | `esp32-wifi-provision` |
| OTA 升级 | `esp32-ota` |
| 低功耗（Deep Sleep/light sleep） | `esp32-lowpower` |
| 安全启动 / Flash 加密 | `esp32-secureboot` |
| coredump / JTAG / GDB 调试 | `esp32-debug` |
| 芯片选型（ESP32 系列对比） | `esp32-variants` |
| 交叉工具链（通用于两条链路） | `fw-toolchain` |
| 无板模拟（QEMU/Wokwi，先跑通再上板） | `fw-emulation` |
| 硬件验收（HIL 在环测试） | `fw-hil-testing` |
| 发布流程 / 产物命名 / 校验和 | `fw-release-gate` |
| **Rust no_std / embedded-hal / Embassy / RTIC 固件** | **包外：`rust-skills/rust-embedded`（refuse 并移交）** |

OpenWrt 内部的三级链路怎么选（官方 IB 直出 vs ophub 重打包 vs 仅运行时配置），读 [routing-openwrt](references/routing-openwrt.md)；ESP32 链路的选择树读 [routing-esp32](references/routing-esp32.md)。

## Workflow

1. **分型**：按 Determine Task Type 判 1/2/3/4；拿不准时按 [task-typing](references/task-typing.md) 的判据追问。
2. **问平台**：确认目标设备/芯片与交付物类型（见 Prerequisites）。
3. **查路由表**：命中一行 → 加载对应 Skill 并把上下文（平台、版本、约束）带过去。
4. **跨链路任务拆分**：如"给 N1 做带自定义服务的固件"= `openwrt-image-build`（rootfs 侧）+ `openwrt-amlogic-remake`（eMMC 镜像侧），按链路顺序串行移交，不混在一个 Skill 里做。
5. **拒绝与移交**：Rust no_std 请求 → 明确说明本包不覆盖，移交 `rust-skills/rust-embedded`；OpenWrt/ESP32 之外的平台（如 bare-metal STM32 裸机 C 固件）→ 说明超界，仅给通用建议并指向官方文档。

## Validation Gates

- 路由结果必须能对上表中某一行；对不上的，明确说"超界"而不是硬套。
- 移交时复述三要素：目标平台、交付物类型、已确认的约束/基线。
- 任何产物声称"可用"前检查：是否有硬件证据？没有 → 标注 `Build Verification Only` 或 `Pending HIL`。

## Pitfalls

1. **不要**在没问平台与交付物类型前就开始"帮忙写配置"——OpenWrt 的 UCI 配置和 ESP-IDF 的 sdkconfig 是两个世界。
2. **不要**把 N1/Amlogic 盒子的需求路由给 `openwrt-image-build` 就结束——官方 IB 直出不含盒子 eMMC 布局，必须继续移交 `openwrt-amlogic-remake`。
3. **不要**用本包接 Rust no_std 任务——宁可拒绝并移交 `rust-skills/rust-embedded`，也不要用通用 C/ESP-IDF 知识硬答。
4. **不要**编造 PROFILE/DTB/分区偏移——不确定就路由到运行时核验。
5. **不要**把"构建成功"汇报成"刷机可用"。

## Official Sources

- [OpenWrt 官方文档](https://openwrt.org/docs/start)
- [OpenWrt Table of Hardware](https://openwrt.org/toh/start)
- [OpenWrt Image Builder 文档](https://openwrt.org/docs/guide-developer/imagebuilder)
- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
- [Espressif ESP32 产品选型](https://www.espressif.com/en/products/socs)
- [ophub/amlogic-s9xxx-openwrt](https://github.com/ophub/amlogic-s9xxx-openwrt)
- [Agent Skills Specification](https://agentskills.io/specification)

## Privacy

本 Skill 只做本地分型与路由，不采集、不存储、不外发用户数据、设备序列号或凭据。访问上述官方链接须遵守用户环境的网络策略。
