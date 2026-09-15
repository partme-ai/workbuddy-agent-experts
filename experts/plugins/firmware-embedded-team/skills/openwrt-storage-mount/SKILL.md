---
name: openwrt-storage-mount
license: Apache-2.0
description: "Explain and configure OpenWrt block-device storage: hot-plug auto-mount for USB disks, fstab UCI generation via `block detect`, the hotplug event flow (kernel uevent → procd hotplug.json → /sbin/hotplug-call → /etc/hotplug.d/<subsystem>/ sourced in lexical order), and storage/filesystem kernel module selection (kmod-usb-storage, kmod-fs-ext4/ntfs3/vfat/btrfs, block-mount/fstools). Use when users ask how to make an inserted USB drive auto-mount, how to write /etc/config/fstab, why a disk is not mounted, how hotplug.d scripts work, or which kmod packages storage needs. Do not mount from a custom hotplug script that competes with block-mount's 10-mount — follow-up scripts numbered >10 that only add non-mount actions are the convention. Building these packages into a firmware image hands off to openwrt-image-build; init.d/procd service scaffolding hands off to openwrt-procd-init."
---

# OpenWrt 块设备存储与挂载

先理解事件流与所有权（谁负责挂载），再动手。**block-mount 已拥有挂载权**；自定义 hotplug 脚本只做补充动作，绝不二次挂载。

## Determine Task Type

1. **配置自动挂载**（fstab UCI + block 命令）—— 走 Workflow A。
2. **写 hotplug 附加脚本**（点灯/扫描/通知等补充动作）—— 走 Workflow B，先读 [hotplug-flow](references/hotplug-flow.md)。
3. **选 kmod**（USB 控制器/文件系统）—— read [kmod-storage](references/kmod-storage.md)。
4. **排查"插了盘没反应"**—— 沿事件流逐段定位 → read [hotplug-flow](references/hotplug-flow.md)。

## Prerequisites / Preflight

SSH 到设备逐项运行时核验：

- block 命令存在：`command -v block`。fstools 在 DEFAULT_PACKAGES（include/target.mk L21-34），任何官方镜像都有 `/sbin/block`。
- block-mount 是否已装：`opkg list-installed | grep block-mount` 或 `apk info -e block-mount`（25.12 源码树 opkg/apk 两套并存，取决于构建配置 `USE_APK`，config/Config-build.in L71）。nas 设备型默认含 block-mount（target.mk L44-48），router 型默认**不含**（L52-61）。
- USB 链路可见性：`ls /sys/class/block/`、`lsusb`、`dmesg | tail -20`。
- 内核版本：`uname -r` —— kmod 包版本必须与之精确匹配，跨版本模块拒绝加载。

## Offline Baseline

- OpenWrt upstream-refs：**25.12.5**（走读 2026-09-02，不自动更新）。文件路径与行号均指该快照。
- fstools 包安装物（package/system/fstools/Makefile L112-117）：
  - `/etc/hotplug.d/block/10-mount` ← files/mount.hotplug
  - `/etc/hotplug.d/block/00-media-change` ← files/media-change.hotplug
  - `/etc/uci-defaults/10-fstab` ← files/fstab.default
  - `/etc/init.d/fstab` ← files/fstab.init（START=11）
- 已核验佐证：procd hotplug.json、base-files sbin/hotplug-call、kernel modules fs.mk/usb.mk。

## Contracts（事件流与所有权，不确定禁止编造）

1. **热插拔事件流**：内核 uevent → procd 按 hotplug.json 规则匹配 → `exec /sbin/hotplug-call %SUBSYSTEM%`（procd hotplug.json L47、L84-85）→ hotplug-call 对 `/etc/hotplug.d/$1/*` 按 `ls` 字序逐个 source（base-files/files/sbin/hotplug-call）。逐段细节见 references/hotplug-flow.md。
2. **挂载所有权**：block-mount 的 `10-mount` 收到 add/remove 即执行 `/sbin/block hotplug`（mount.hotplug 全文一行），挂什么由 fstab UCI 决定。
3. **首启契约**：`/etc/uci-defaults/10-fstab` 仅当 `/etc/config/fstab` 不存在时执行 `block detect > /etc/config/fstab`（fstab.default 全文一行）。
4. **开机契约**：`/etc/init.d/fstab` START=11：`boot() → /sbin/block mount`，`stop() → /sbin/block umount`（fstab.init）。
5. **kmod 契约**：存储与文件系统模块经 AUTOLOAD/AutoProbe 自动加载（kmod-usb-storage `AutoProbe usb-storage`，usb.mk L1093-1100；fs-btrfs `AutoLoad,30`，fs.mk L67-77）。包矩阵见 references/kmod-storage.md。
6. **文件系统能力一句话**：kmod-fs-ntfs3 / kmod-fs-exfat 让 NTFS/exFAT"能挂能写"；但坏块隔离与自愈等数据保护是 ext4（及 btrfs）这类原生文件系统的能力，长期数据盘优先 ext4。

## Capability Boundaries + Hand-off

不做：构建期把包/文件烧进固件；init.d 服务脚手架；RAID/LVM 与 Samba/NFS 等上层服务教学。

| User Intent | Assigned To |
|---|---|
| 构建期预置 block-mount/kmod/自定义 fstab/50- 脚本进镜像 | `openwrt-image-build` |
| procd init.d 服务、rc.common 脚手架 | `openwrt-procd-init` |

## Workflow A：插 U 盘自动挂载

1. **装包**（运行时安装；构建期预置 hand-off `openwrt-image-build`）：

   ```sh
   opkg update
   opkg install block-mount kmod-usb-storage kmod-fs-ext4
   # NTFS 盘加 kmod-fs-ntfs3；exFAT 加 kmod-fs-exfat；btrfs 加 kmod-fs-btrfs
   ```

2. **生成 fstab 草稿**：`block detect > /etc/config/fstab`（与首启 uci-defaults 10-fstab 同源逻辑，fstab.default）。
3. **编辑目标条目**：

   ```sh
   uci set fstab.@mount[-1].target='/mnt/sda1'
   uci set fstab.@mount[-1].enabled='1'
   uci commit fstab
   ```

   uuid 与 device 属性二选一、字段语义见 references/fstab-uci.md。
4. **立即挂载并验证**：`block mount && df -h`；`block info` 核对设备识别与文件系统类型。
5. **重启验证开机链路**：重启后 `df -h` 仍在（S11 `block mount` 生效）；`logread | grep -i mount`。

## Workflow B：附加 hotplug 脚本（只做补充）

协作军规：**不自写挂载逻辑**。10-mount 已负责挂载；你的脚本若也 mount，会与 `block hotplug` 竞争（双挂载、互踩 umount）。正确模式：

1. **序号 >10**（10-mount 之后执行）：`/etc/hotplug.d/block/50-<name>`。
2. **只做 block-mount 不做的事**：健康扫描、点灯、通知、logger 打点。
3. **脚本模板**：

   ```sh
   #!/bin/sh
   # /etc/hotplug.d/block/50-my-disk — 附加动作，绝不 mount（10-mount 已负责）
   [ "$ACTION" = "add" ] || exit 0
   case "$DEVNAME" in sd[a-z]) : ;; *) exit 0 ;; esac
   logger -t my-disk "new disk $DEVNAME"
   ( [ -x /usr/bin/my-disk-hook ] && /usr/bin/my-disk-hook "/dev/$DEVNAME" >/dev/null 2>&1 & )
   exit 0
   ```

   该模式来自实测仓库真实例子 `50-tinynas-disk`（openwrt-imagebuilder/common/tinynas-files/etc/hotplug.d/block/）：文件头注释即军规（"不挂载！block-mount 10-mount 已负责挂载"），仅对 `rotational=1` 的 sdX 后台排队快速扫描，且工具存在才调用、不存在则 logger 记录。
4. **调试**：脚本内 `env > /tmp/hotplug.env` 抓事件变量；`logread` 看 hotplug-call 输出。事件流逐段排查见 references/hotplug-flow.md。

## Validation Gates

按证据分层，无设备时所有结论标 `Pending HIL`：

1. **事件到达**：插入设备 `logread -f` 可见 hotplug 活动；`ls /sys/class/block/` 出现新盘。
2. **fstab 生成**：`uci show fstab` 每条 mount 有 target、uuid/device 且 enabled=1。
3. **挂载成功**：`df -h` 出现 target；`touch <target>/.rw && rm <target>/.rw` 写入测试通过。
4. **重启保持**：重启后 df 仍在 —— 证明 S11 `block mount` 生效，而不是只靠本次手动 mount。
5. **失败特征**：`dmesg` 出现 unknown filesystem / `block mount` 静默不挂 → 通常是缺 fs kmod，回 Workflow A 第 1 步核对包矩阵。

## Pitfalls

- **不要**自写 hotplug 挂载脚本与 10-mount 竞争 —— 挂载的唯一事实源是 fstab UCI；双挂载/umount 竞争会造成数据损坏风险。
- **不要**用 ≤10 的序号 —— `00-media-change`、`10-mount` 已被 fstools 占用，早于 10 执行会在 `block hotplug` 之前跑。
- **不要**在 hotplug 脚本里同步长跑 —— hotplug-call 按字序同步 source，会阻塞后续脚本与 procd 事件处理；后台化。
- **不要**假设 `/etc/config/fstab` 一定存在 —— 它由首启 uci-defaults 10-fstab 条件生成；容器/自制镜像可能没有，先 `block detect`。
- **不要**在同一条目混用 uuid 与 device —— 二选一，语义见 references/fstab-uci.md。
- **不要**乱装不匹配的 kmod —— 版本必须等于 `uname -r`，跨版本 insmod 直接拒绝。
- **不要**把 NTFS/exFAT 盘当长期数据盘 —— 可挂可写，但坏块隔离与自愈是 ext4 原生能力。

## Official Sources

- <https://openwrt.org/docs/guide-user/storage/wextexternal>（官方外部存储指南）
- <https://openwrt.org/docs/guide-user/base-system/hotplug>（官方 hotplug 指南）
- <https://git.openwrt.org/?p=project/fstools.git>（block/fstools 上游源码）
- <https://downloads.openwrt.org/releases/25.12.5/>（包索引，按目标平台核对 kmod 版本）

## Privacy

- 不采集、不外发用户数据；`block detect` 输出仅含磁盘 UUID/型号等设备事实。
- 排查输出（dmesg/logread）可能含内网拓扑与主机名：留在本地分析，回复中不原样粘贴大段日志。
- 磁盘序列号/UUID 属设备标识，建议用户外发前打码。
