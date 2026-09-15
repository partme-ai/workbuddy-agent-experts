# 任务分型判据（task-typing）

read-when：用户意图模糊、同时提及多个领域、或路由表无法唯一命中时。

## 按交付物分型（权威判据）

问自己："用户拿到什么东西才算任务完成？"

| 最终交付物 | 任务类型 | 路由 |
|---|---|---|
| 可刷写的 OpenWrt 镜像文件（.img.gz/.bin） | Linux 网关固件 | `openwrt-image-build` |
| 盒子可写的 eMMC 镜像（N1/Amlogic/Rockchip/Allwinner） | Linux 网关固件（重打包链） | `openwrt-amlogic-remake`（rootfs 侧先走 `openwrt-image-build`） |
| 已运行设备上的配置变更（UCI/init.d/挂载） | 仅运行时配置 | 对应 openwrt-* 运行时 Skill，无需重新构建镜像 |
| ESP32 片上固件（.bin/.elf + 分区表） | MCU 固件 | `esp32-idf` 起步 |
| "先在没板子的情况下跑通逻辑" | 模拟验证 | `fw-emulation` |
| Rust `#![no_std]` 工程 / embedded-hal 驱动 / Embassy | 超界 | `rust-skills/rust-embedded` |

## 易混淆场景仲裁

- **"给 N1 刷机"**：交付物是 eMMC 镜像 → 主路由 `openwrt-amlogic-remake`；若还要预装自定义服务/文件，rootfs 侧先走 `openwrt-image-build`，再把 rootfs.tar.gz 交给 remake 链。
- **"路由器加个开机自启脚本"**：设备已在跑 → `openwrt-procd-init`（运行时做法）；若要求"固化进镜像"→ `openwrt-image-build` 的 FILES= 注入，init 脚本规范仍参照 procd-init。
- **"配网"**：ESP32 上指 Wi-Fi 配网 → `esp32-wifi-provision`；OpenWrt 上通常指首启无线配置 → `openwrt-uci-defaults`。按平台词消歧。
- **"OTA"**：ESP32 → `esp32-ota`；OpenWrt → sysupgrade 流程（`openwrt-image-build` 产 sysupgrade 镜像 + `fw-release-gate` 发布）。
- **"低功耗"**：ESP32 睡眠模式 → `esp32-lowpower`；x86/盒子场景通常是"待机功耗"问题，超 ESP32 低功耗 Skill 的边界，按运行时配置处理。

## 追问模板（信息不足时用）

1. "目标硬件是什么？设备型号/芯片型号？"
2. "你要的是镜像文件、还是改一台已在运行的设备？"
3. "有没有硬件在手上？没有的话要不要先走模拟？"
4. （ESP32）"工程用的是哪个 ESP-IDF 版本？"
5. （OpenWrt）"目标 OpenWrt 版本？设备在官方 Table of Hardware 里吗？"

## 拒绝话术（Rust no_std）

"firmware-skills 包覆盖 OpenWrt 网关固件与 ESP-IDF（C 环境）MCU 固件，不覆盖 Rust no_std 固件。请改用 `rust-skills/rust-embedded`，它覆盖 target/runtime 选择、embedded-hal 驱动、Embassy/RTIC、probe-rs 烧写与硬件验收证据。"

不要用通用嵌入式 C 知识硬答 Rust no_std 问题。
