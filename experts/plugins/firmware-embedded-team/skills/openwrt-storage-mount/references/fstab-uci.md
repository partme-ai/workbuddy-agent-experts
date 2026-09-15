# fstab UCI 与 block 命令速查

来源：`package/system/fstools/files/`（fstab.default、fstab.init、mount.hotplug）与 block 工具行为（OpenWrt 25.12.5 快照，走读 2026-09-02）。

## 三份种子文件的分工

| 文件 | 安装为 | 行为（原文口径） |
|---|---|---|
| fstab.default | /etc/uci-defaults/10-fstab | `[ ! -f /etc/config/fstab ] && ( block detect > /etc/config/fstab )` —— 首启一次性生成草稿 |
| fstab.init | /etc/init.d/fstab（START=11） | `boot() → /sbin/block mount`；`stop() → /sbin/block umount`；start/restart 为空操作 |
| mount.hotplug | /etc/hotplug.d/block/10-mount | add/remove → `/sbin/block hotplug`（热插时按 fstab 现挂） |

关键推论：uci-defaults 只在 fstab 不存在时写一次 —— 用户的修改不会被覆盖；反之自制镜像若预置了 fstab，10-fstab 自动跳过。

## `block detect` 生成的 UCI 骨架

`block detect > /etc/config/fstab` 会为每个分区/盘生成 config 段（`config 'global'` + 每个可挂块一条 `config 'mount'`，swap 为 `config 'swap'`）。典型条目字段：

```text
config mount
        option target '/mnt/sda1'        # 挂载点
        option uuid 'xxxx-xxxx'           # 按文件系统 UUID 匹配（推荐）
        option device '/dev/sda1'         # 按设备节点匹配（与 uuid 二选一）
        option fstype 'ext4'
        option options 'rw,sync'
        option enabled '0'                # detect 生成的是 0，必须手工置 1
```

要点：

- **uuid 与 device 二选一**：uuid 跟盘走（换口/换序不变），device 跟槽位走（换盘位即失配）。固定存储用 uuid。
- detect 输出的 enabled 恒为 0 —— 不改直接 `block mount` 不会挂它。
- `option enabled '1'` + `uci commit fstab` 后才会被 `block mount` / `block hotplug` 采纳。

## 常用命令

```sh
block detect | tee /tmp/fstab.draft      # 生成草稿先看，不直接覆盖
block info                               # 每个块设备的 UUID/TYPE/挂载状态
block info /dev/sda1                     # 单设备
block mount                              # 按 fstab enabled=1 全量挂载（= S11 boot 行为）
block umount                             # 全量卸载（= init stop）
```

`block hotplug`（10-mount 内部调用）语义与 mount 类似，但只处理刚发生事件的那块盘，供热插路径使用——不要手动模拟它，测试用 `block mount`。

## 手工配置一条自动挂载

```sh
block detect > /etc/config/fstab         # 首次（已有则跳过，勿覆盖手工配置）
uci set fstab.@mount[-1].target='/mnt/sda1'
uci set fstab.@mount[-1].enabled='1'
uci commit fstab
block mount && df -h                     # 立即验证
```

重启后再 `df -h` 一次 —— 只有重启后仍在，才证明走的是 S11 `block mount`，而不是本次手动残留。

## 常见坑

- 覆盖式 `block detect > /etc/config/fstab` 会冲掉已做的手工定制 —— 已有 fstab 时用 `block detect` 仅作草稿比对。
- enabled 忘记置 1 → 插拔与重启都不挂，误判为"hotplug 坏了"。
- target 目录不存在时 block 会自建；但 NFS/Samba 等网络挂载不走 fstools fstab，别混配。
- 排查顺序永远是：kmod（盘可见）→ fstab（条目 enabled）→ block mount（手动触发）→ 重启（S11 链路）。
