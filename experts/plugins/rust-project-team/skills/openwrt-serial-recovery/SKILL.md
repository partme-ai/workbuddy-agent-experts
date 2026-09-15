---
name: openwrt-serial-recovery
license: Apache-2.0
description: Triage and recover Amlogic-based TV-box devices (e.g. Phicomm N1 / S905D) running OpenWrt through a three-tier recovery ladder - USB/SD re-flash while the system or U-Boot still works, TTL UART into the U-Boot command line, and hardware-level short-circuit/programmer recovery (declared out of scope with routing instead). Cover brick grading, software-first ordering, ophub rescue tooling (openwrt-ddbr, kernel rescue via Amlogic Service, USB Burning Tool prerequisites), USB-over-eMMC boot priority, and runtime log triage with logread/dmesg for devices that still boot. Use when the user says 盒子刷砖了 / 起不来了 / 无法启动 / 想救回设备, asks whether TTL 串口 can still reach the box, or needs to decide between re-flash, serial, and hardware recovery. Refuses to invent board-specific shorting points, pinouts, or rescue parameters - those are marked Pending HIL and routed to official schematics, the ophub device matrix, or fw-hil-testing
---

# OpenWrt Serial and Recovery (Amlogic Boxes)

Recovery work runs on degraded information. This skill gives a decision ladder with explicit evidence confidence; it never fabricates board-specific parameters. Anything not verifiable from the cited sources is marked `Pending HIL / 需按设备实测`.

## Determine Task Type

| If the device... | Path |
|---|---|
| Still boots (from eMMC or USB), services misbehave | Runtime triage → Workflow R |
| Does not boot from eMMC, but USB/SD boot works | Ladder Tier 1 → Workflow T1 |
| Boots nothing; needs U-Boot command line | Ladder Tier 2 → Workflow T2 |
| No display output, no USB enumeration; needs short-circuit/programmer | Ladder Tier 3 → refuse specifics, route (Workflow T3) |

## Prerequisites / Preflight

Ask for / gather before recommending anything:

1. Exact board model and SoC (e.g. "Phicomm N1, S905D" vs "小米盒子3, S905-H" — eMMC writability differs, see Contracts).
2. What still happens: HDMI output? `=>` prompt on screen? USB device enumeration on the host? Power LED behavior?
3. What media is available: USB stick with a known-good image, TTL adapter, backup image (`/ddbr/BACKUP-arm-64-emmc.img.gz`)?

Do not proceed to Tier 2/3 advice while a Tier 1 path is untried.

## Offline Baseline

- OpenWrt convention baseline 25.12.5 (走读 2026-09-02).
- ophub `amlogic-s9xxx-openwrt` documents verified against the local checkout, upstream HEAD `c593d56` (documents/README.cn.md §9 SOS, §10.8, §10.9, §10.10). Does not auto-update.
- Community-experience sources (labeled 社区经验， lower confidence than project docs): local chat records on N1 vs 小米盒子3 flashing (USB port near HDMI preferred boot; eMMC write via `armbian-install`/`openwrt-install-amlogic`).

## Contracts

- N1 (S905D): community records report eMMC is writable and the standard flow is USB boot → one-command eMMC install; recovery from USB is therefore usually non-invasive (社区经验).
- 小米盒子3 (S905-H): community records report eMMC is not writable by the standard ophub flow and USB-stick-only operation; deeper recovery historically needed opening the case and TTL (社区经验).
- USB boot has priority over eMMC on these boxes when both are bootable; ophub documents the `boot.scr` rename workaround for boxes that refuse USB boot (项目文档， README.cn §10.10.2).
- UART parameters: **115200 8N1, 3.3 V TTL is the common Amlogic default — 常见值，以板实测为准 (`Pending HIL`)**. Never feed 5 V logic into a board pad.
- Anti-hallucination red line: this skill does not state shorting-point locations, board pinouts, partition offsets, or DTB names for any specific board. All such values are `Pending HIL / 需按设备实测`.

## Capability Boundaries and Hand-off

| User intent | Route to |
|---|---|
| Supervised hardware verification of any `Pending HIL` item | `fw-hil-testing` |
| Rebuild/repackage the image being re-flashed | `openwrt-amlogic-remake`, `openwrt-image-build` |
| Fix services/config after the device boots again | `openwrt-procd-init`, `openwrt-uci-defaults` |
| Storage/mount problems that look like "disk dead" | `openwrt-storage-mount` |

Tier 3 board specifics are permanently out of scope for this skill; see Workflow T3's refusal rule and the evidence-confidence table in [Recovery Ladder](references/recovery-ladder.md).

## Recovery Ladder (software-first)

| Tier | Entry condition | Action class | Evidence confidence |
|---|---|---|---|
| 1. USB/SD re-flash | Device powers, USB boot works (or eMMC system partially works) | Rewrite from USB, rescue kernel via Amlogic Service, restore ddbr backup, re-run eMMC install | 项目文档 + 社区经验， per item in [Recovery Ladder](references/recovery-ladder.md) |
| 2. TTL U-Boot | No usable OS, but U-Boot prompt reachable over serial | Inspect env/boot media from U-Boot; boot from USB via U-Boot commands | 命令面为通用 U-Boot 能力；参数按板 `Pending HIL` |
| 3. Short-circuit / programmer | No HDMI, no USB enumeration | USB Burning Tool line-flash with short-circuit, or CH341A-class programmer | 项目文档 covers the *procedure class* with one example device; **this skill does not provide board-specific shorting points** |

Tier 3 execution is outside this skill's safe scope: route the user to the official board schematic/device wiki, the ophub tools matrix, and `fw-hil-testing` for supervised hardware work.

## Workflow R — runtime triage (device still boots)

1. `logread | tail -50` — service failures, respawn storms (procd messages).
2. `dmesg | tail -50` — storage/IO errors, USB re-enumeration, thermal events.
3. `/etc/init.d/<svc> status` per suspect service; `ubus call service list | head -40` for the live picture.
4. Fix at the config layer first (→ `openwrt-procd-init`, `openwrt-uci-defaults`); only a non-booting device drops to the ladder.

## Workflow T1 — USB/SD re-flash

1. Write a known-good image to USB/SD on the host; verify checksums.
2. Boot from USB before touching eMMC — USB has boot priority over eMMC (README.cn §10.10.2). Community note for N1: the USB port nearer the HDMI connector is the one that boots preferentially (社区经验).
3. If the box still boots eMMC into OpenWrt but refuses USB: rename eMMC `/boot/boot.scr` to `boot.scr.bak` and retry (README.cn §10.10.2 — project-documented workaround).
4. If eMMC OpenWrt boots but the kernel is broken after an update: rescue via LuCI `Amlogic Service` (晶晨宝盒) → 救援内核， or `openwrt-kernel -s [disk]` in a terminal — the ophub document spells the tool `openwer-kernel`; confirm the exact binary on-device with `which openwrt-kernel openwer-kernel` before running (README.cn §9).
5. Android-TV backup/restore via `openwrt-ddbr` (`b` backup → `/ddbr/BACKUP-arm-64-emmc.img.gz`, `r` restore) (README.cn §10.8.1).
6. Only after USB boot is stable, reinstall to eMMC (N1-class: `armbian-install` / `openwrt-install-amlogic`, 社区经验).

## Workflow T2 — TTL into U-Boot

1. Hardware: 3.3 V USB-TTL adapter; **115200 8N1, no flow control is the common default — verify against the board (`Pending HIL`)**. TX→RX crossed, GND common. Pin locations are board-specific: do not guess; use the board's schematic/community photos and mark unverified findings accordingly.
2. Host terminal: `screen /dev/ttyUSB0 115200` or `picocom -b 115200 /dev/ttyUSB0` (or PuTTY on Windows).
3. Power cycle and watch the console. A prompt ending in `=>` is U-Boot.
4. ophub documents a specific failure class: after writing mainline U-Boot, some boxes stop booting with output ending in `=>`; the documented fix is soldering a 5-10 K pull-up (RX–GND) or pull-down (3.3 V–RX) resistor on TTL (README.cn §10.9). Board-specific soldering is hardware work → confirm against the project doc photos and `fw-hil-testing`.
5. From U-Boot, generic capabilities (env inspection, loading a kernel from USB/mmc) apply, but exact commands depend on the board's U-Boot build — treat any specific command sequence as `Pending HIL` until observed on the device.

## Workflow T3 — short-circuit / programmer (out of scope, routed)

When display is black and USB is not enumerated, the recovery class is: restore the stock Android system via Amlogic USB Burning Tool + a short-circuited boot, then re-flash OpenWrt; ophub documents the procedure class with an x96max+ example and links device firmware/shorting diagrams to its tools release (README.cn §10.8.2). This skill refuses to state any board's shorting points from memory: route to the official schematic, the ophub tools matrix, and `fw-hil-testing` (`Pending HIL` for every specific board).

## Validation Gates

- T1 success: device boots the re-flashed image from eMMC with the USB stick removed; `logread` clean of mount/kernel errors.
- T2 success: serial console shows U-Boot output; a rescue action observed end-to-end.
- T3: out of scope; success claims require the supervised HIL record — never assert recovery you did not observe.
- All runtime fixes: re-run Workflow R checks and the service-level Validation Gates of `openwrt-procd-init`.

## Pitfalls

- Do not jump to short-circuit advice while USB boot is untried; software-first is the ladder's ordering.
- Do not state a board's shorting points, TTL pinout, or UART params as fact without a source; label them `Pending HIL / 需按设备实测`.
- Do not flash a random "N1 image" to other SoCs; model/SoC mismatches are a leading cause of the bricks being recovered.
- Do not restore eMMC from a ddbr backup without confirming the backup predates the failure you are escaping.
- Do not connect 5 V serial logic to a 3.3 V board pad.
- Do not promise "eMMC 写入" for SoCs where the standard flow does not support it (e.g. S905-H per community records); say which parts are 社区经验.
- Do not treat the doc-spelled `openwer-kernel` as interchangeable with the actual binary name — verify on device first.

## Official Sources

- ophub amlogic-s9xxx-openwrt manual (recovery chapters): https://github.com/ophub/amlogic-s9xxx-openwrt/blob/main/documents/README.cn.md
- ophub tools (Android firmware, burning tool, adb): https://github.com/ophub/kernel/releases/tag/tools
- OpenWrt serial console basics: https://openwrt.org/docs/techref/hardware/port.serial
- U-Boot documentation: https://docs.u-boot.org/en/latest/

## Privacy

This skill does not collect, store, or transmit user data. Serial logs, dmesg output, and ddbr backups can contain hostnames, MAC addresses, credentials, and user data from eMMC — treat them as sensitive; scrub logs before sharing, and store backups encrypted.
