# 热插拔事件流（uevent → procd → hotplug-call → hotplug.d）

来源：`package/system/procd/files/hotplug.json`、`package/base-files/files/sbin/hotplug-call`、`package/system/fstools/files/mount.hotplug`（OpenWrt 25.12.5 快照，走读 2026-09-02）。

## 四段事件流

```text
内核 uevent (ACTION/SUBSYSTEM/DEVNAME/MAJOR/MINOR…)
  → procd 解析 hotplug.json 规则
  → 匹配规则执行动作，典型为 exec /sbin/hotplug-call <subsystem>
  → hotplug-call 按 ls 字序 source /etc/hotplug.d/<subsystem>/* 每个脚本
```

1. **procd 规则文件** hotplug.json（全文 88 行）：
   - `case ACTION` 块处理 add/remove 两大分支（makedev、load-firmware 等）。
   - add 分支内含 FIRMWARE 处理：`exec /sbin/hotplug-call %SUBSYSTEM%` + `load-firmware`（L44-48）。
   - 专项规则：button → `/etc/rc.button/%BUTTON%`；usb-serial 且 DEVNAME 匹配 `^ttyUSB|^ttyACM` → `hotplug-call tty`（L82）。
   - **兜底规则（L83-86）**：只要 `/etc/hotplug.d/%SUBSYSTEM%/` 目录存在，就 `exec /sbin/hotplug-call %SUBSYSTEM%` —— block 事件走的就是这条（因为 fstools 装了 `/etc/hotplug.d/block/`）。
2. **hotplug-call**（base-files）：`export HOTPLUG_TYPE=$1` 后 `for script in $(ls /etc/hotplug.d/$1/*)`，逐个子 shell source（`[ -f $script ] && . $script`）。
   - **字序 = ls 字典序**：`00-` → `10-` → `50-` 依次执行。
   - 每个 hotplug 脚本运行在独立子 shell；事件变量（ACTION/DEVNAME/SUBSYSTEM…）已导出。
3. **block-mount 的 10-mount**：`[ "$ACTION" = "add" -o "$ACTION" = "remove" ] && /sbin/block hotplug`（mount.hotplug 全文一行）——挂载决策交给 fstab UCI。
4. **00-media-change**：光介质变更事件，同样属于 fstools 所有序（Makefile L117）。

## fstools 所有序速览（package/system/fstools/Makefile L112-117）

| 安装路径 | 语义 |
|---|---|
| /etc/hotplug.d/block/00-media-change | 介质变更 |
| /etc/hotplug.d/block/10-mount | add/remove → `block hotplug`（挂载所有者） |
| /etc/uci-defaults/10-fstab | 首启 `block detect > /etc/config/fstab`（仅当不存在） |
| /etc/init.d/fstab | START=11，boot→`block mount`，stop→`block umount` |

## 为什么附加脚本必须 >10 且不挂载

- 字序保证 `50-` 在 `10-mount` 之后执行：此时盘已被 block 挂上（或至少 hotplug 已处理过），补充逻辑拿到的是"挂载后"世界。
- 若 `50-` 自己 mount：与 `block hotplug` 各自决策，产生双挂载/挂到不同点/umount 互踩 —— fstab UCI 是挂载的唯一事实源。
- 真实范本：`openwrt-imagebuilder/common/tinynas-files/etc/hotplug.d/block/50-tinynas-disk` —— 只对 `rotational=1` 的 sdX 后台排队健康扫描，工具存在才调用；文件头注释："不挂载！block-mount 10-mount 已负责挂载"。

## 逐段排查"插盘没反应"

| 症状 | 检查 | 手段 |
|---|---|---|
| 盘没出现 | USB/存储 kmod 没装 | `lsusb`、`dmesg`（看尾部）、`ls /sys/class/block/` |
| 块设备有、无挂载 | fstab 缺条目/enabled=0 | `block detect`、`uci show fstab`、`block mount` |
| 事件没进 50- 脚本 | SUBSYSTEM 不是 block / 目录名错 | 脚本里 `env > /tmp/hotplug.env`；确认放在 `/etc/hotplug.d/block/` |
| 50- 脚本没执行完 | 同步阻塞被后续事件影响 | 全部动作后台化 `( cmd & )` |
| 重启后不挂 | 只做了手动 mount，没走 fstab | 回 fstab UCI（见 fstab-uci.md），重启验证 |
