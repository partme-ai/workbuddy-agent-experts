# Recovery Ladder: Tiers, Conditions, Evidence

Sources: ophub `amlogic-s9xxx-openwrt/documents/README.cn.md` @ upstream HEAD `c593d56` (§9, §10.8, §10.9, §10.10) — 项目文档；N1/MiBox-3 community chat records — 社区经验. Walkthrough 2026-09-02.

## Brick grading (decide before acting)

| Grade | Symptoms | Start at |
|---|---|---|
| Soft brick | Boots from eMMC or USB; wrong/old system; kernel panic mid-boot | Tier 1 |
| Boot-media brick | Refuses USB with eMMC present; screen shows U-Boot output ending `=>` | Tier 1 workaround → Tier 2 |
| Hard brick | Black screen, no USB enumeration, no serial output | Tier 3 (routed, out of scope) |

Principle: 先软后硬 — never advance a tier while the previous tier has untried paths.

## Tier 1 — USB/SD re-flash

| Action | Condition | Source / confidence |
|---|---|---|
| Boot from USB stick; USB has boot priority over eMMC | Box powers at all | README.cn §10.10.2 — 项目文档 |
| N1: use the USB port **nearer the HDMI connector** (preferentially recognized for boot) | N1-class hardware | 社区经验 |
| Rename eMMC `/boot/boot.scr` → `boot.scr.bak` to force USB boot | eMMC OpenWrt still bootable but USB boot refused | README.cn §10.10.2 — 项目文档 |
| Kernel rescue: LuCI `Amlogic Service`(晶晨宝盒) → 救援内核； or terminal `openwrt-kernel -s [disk]` (doc spells `openwer-kernel` — verify with `which` on device) | eMMC boots, kernel broken after update | README.cn §9 — 项目文档 |
| Android TV backup/restore: `openwrt-ddbr`, `b`=backup → `/ddbr/BACKUP-arm-64-emmc.img.gz`, `r`=restore | Stock Android worth keeping/restoring | README.cn §10.8.1 — 项目文档 |
| Reinstall to eMMC: `armbian-install` / `openwrt-install-amlogic` (N1/S905D) | After USB boot is stable | 社区经验 |
| MiBox-3 (S905-H): eMMC write not supported by the standard flow; USB-stick operation only | MiBox-3 | 社区经验 |

## Tier 2 — TTL U-Boot

| Item | Value | Source / confidence |
|---|---|---|
| Adapter | USB-TTL, **3.3 V** logic; 5 V will damage the pad | 通用硬件常识 |
| Baud/format | 115200 8N1, no flow control | 常见 Amlogic 默认 — `Pending HIL / 需按板实测` |
| Wiring | TX→RX crossed, GND common; pin locations board-specific | 通用常识 + `Pending HIL` for pins |
| Mainline U-Boot no-boot class | Screen output ends `=>`; documented fix: solder 5-10 K pull-up (RX–GND) or pull-down (3.3 V–RX) on TTL | README.cn §10.9 — 项目文档（含 X96 Max Plus V4.0 示例图） |
| U-Boot command sequences | Generic env/mmc/usb load capabilities; exact commands depend on the board's U-Boot build | `Pending HIL` until observed |

## Tier 3 — short-circuit / line flash (routed)

- Procedure class (README.cn §10.8.2 — 项目文档， x96max+ example): Amlogic USB Burning Tool + USB A-A cable + paperclip shorting; erase flash + bootloader; remove short when the progress bar moves; restores stock Android, then re-flash OpenWrt as on first install.
- **Specific shorting points: not provided by this skill.** Board-specific diagrams exist in the ophub tools release and device wikis; every specific-board answer here is `Pending HIL / 需按设备实测`.
- Programmer-class recovery (CH341A etc.) is hardware-lab territory → `fw-hil-testing`.

## Decision quick path

1. Boots at all? → Workflow R (runtime triage), then Tier 1.
2. USB tried on the recommended port, with `boot.scr` workaround if applicable? → Tier 2 serial.
3. Serial dead / black screen / no enumeration? → Tier 3 routing, refuse specifics.
