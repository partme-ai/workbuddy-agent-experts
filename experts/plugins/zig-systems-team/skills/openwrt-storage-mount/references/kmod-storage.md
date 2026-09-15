# 存储/文件系统 kmod 选包速查

来源：`package/kernel/linux/modules/usb.mk`、`fs.mk`、`nls.mk`（OpenWrt 25.12.5 快照，走读 2026-09-02）。AUTOLOAD 行号均指这些文件。

## 装机自查顺序

```sh
uname -r                        # kmod 版本必须精确等于它
opkg list-installed | grep kmod # 已装模块（apk 镜像用 apk info -e <pkg>）
lsmod                           # 已加载
dmesg                           # 插盘后的识别记录
```

kmod 版本与内核不匹配时 opkg 依赖即不满足；跨版本 insmod 被内核拒绝（vermagic 不符）。缺哪个装哪个，不要整包乱补。

## USB 存储链路（usb.mk）

| 包 | 作用 | 关键定义 |
|---|---|---|
| kmod-usb-storage | USB Mass Storage → SCSI 块设备 | `DEPENDS:=+kmod-scsi-core`，`AutoProbe usb-storage`（L1093-1100） |
| kmod-usb-storage-extras | 少见 UMS 设备的补充驱动 | DEPENDS +kmod-usb-storage（L1109 起） |
| kmod-usb2 / kmod-usb3 | EHCI / xHCI 主机控制器 | 多数现代设备默认或按目标预选 |
| kmod-usb-ohci / kmod-usb-uhci | 全速/老旧控制器 | AutoLoad 50/51（L282-347） |

绝大多数"U 盘不识别"是缺 kmod-usb-storage 或控制器 kmod；`lsusb` 能看到设备而 `/sys/class/block` 无盘，基本可锁定这一层。

## 文件系统（fs.mk / nls.mk）

| 包 | 挂载对象 | 关键定义 |
|---|---|---|
| kmod-fs-ext4 | ext2/3/4 | DEPENDS +kmod-lib-crc16 +kmod-crypto-hash +kmod-crypto-crc32c（L237-249） |
| kmod-fs-btrfs | btrfs（remake 镜像 p2 即 btrfs） | `AutoLoad,30`；依赖 crc32c/lzo/zlib/raid6/xor/zstd/blake2b/xxhash（L67-77） |
| kmod-fs-vfat | FAT32（U 盘出厂格式） | `AutoLoad,30`；`AddDepends/nls cp437 iso8859-1 utf8`（L644-654） |
| kmod-fs-exfat | exFAT（>4GB 单文件 U 盘） | `AutoLoad,30`；DEPENDS +kmod-nls-base（L204-212） |
| kmod-fs-ntfs3 | NTFS 读写（新内核驱动） | `AutoLoad,80`；`AddDepends/nls`（L577-584） |
| kmod-fs-f2fs | f2fs | `AutoLoad,30`（L262-269） |
| kmod-nls-base | NLS 码表底座 | vfat/exfat/ntfs3 的公共依赖（nls.mk L8-13） |

## AUTOLOAD 机制（为什么装了包就"自动生效"）

- kmod 包元数据带 `AUTOLOAD:=$(call AutoLoad,<序号>,<模块名>)` 或 `AutoProbe`；安装时写入 `/etc/modules.d/<name>`（每行一个模块+参数），开机 kmodloader 按序加载，热插时靠 uevent 请求加载（AutoProbe 路径）。
- 因此运行时装包后**首次**可能需要 `insmod`/热插一次或重启，之后即为全自动。
- 与 remake 的关系：remake 的 refactor_rootfs 就是往 `etc/modules.d/` 写同名文件来补驱动（如 rtl8152、brcmfmac）——同一机制，不是旁门。

## 选包矩阵（按盘的文件系统）

| 盘格式 | 必装 |
|---|---|
| ext4 | kmod-fs-ext4 |
| btrfs | kmod-fs-btrfs |
| FAT32 | kmod-fs-vfat |
| exFAT | kmod-fs-exfat |
| NTFS | kmod-fs-ntfs3 |
| 任意 USB 盘 | kmod-usb-storage（+ 控制器 kmod，通常已含） |

能力边界一句话：NTFS/exFAT 可挂可写，适合交换盘；长期数据盘（坏块隔离、自愈、日志一致性）优先 ext4/btrfs —— 不要把 ntfs3 说成有坏块重映射能力。

## 构建期预置（hand-off）

要把上述包与 fstab/50- 脚本固化进镜像（而非设备上临时 opkg），走 Image Builder PACKAGES/FILES 注入 → `openwrt-image-build`。
