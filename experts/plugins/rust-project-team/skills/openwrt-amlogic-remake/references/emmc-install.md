# eMMC 安装链路（晶晨宝盒 luci-app-amlogic）

来源：`remake` 脚本（HEAD `c593d56`）与 `documents/README.cn.md`（走读 2026-09-02）。

## 核心事实：remake 不自研安装器

镜像的 eMMC 安装能力来自 ophub/luci-app-amlogic（晶晨宝盒），由 remake 在**打包期**注入：

1. download_depends 克隆 ophub/luci-app-amlogic main 分支（`script_repo`，L85；L551-566），克隆重试 10 次、间隔 60s（L481-491）。
2. 把 `root/usr/sbin`（openwrt-install-amlogic、openwrt-kernel 等）拷进 `common-files/usr/sbin` 并对 `openwrt-*` 批量 `chmod +x`（L555-558）。
3. 把 `root/usr/share/amlogic` 拷进 `common-files/usr/share/amlogic` 并 `chmod +x`（L560-564）。
4. extract_openwrt 把 common_files 整体拷入 rootfs（L913）。
5. confirm_version 由 model_database.conf 生成 `model_database.txt`（前 8 列），供 openwrt-install-amlogic 当板型表（L303-308）。

## 打包期写入的运行时配置（refactor_rootfs）

- `etc/config/amlogic`：`amlogic_firmware_tag=<code>_<branch>`、`amlogic_kernel_tags=kernel_<tags>`、`amlogic_kernel_branch=<major.minor>`（L1061-1069）——在线更新按这些 tag 拉包。
- `etc/flippy-openwrt-release`：追加 PLATFORM/MODEL_ID/SOC/FDTFILE/BOARD/KERNEL_TAGS/KERNEL_VERSION/MAINLINE_UBOOT/ANDROID_UBOOT/BUILDER_NAME 等环境事实（L1241-1267），并建符号链接 `etc/ophub-release`（L1269）。
- `/etc/rc.local` 在 `exit 0` 前注入 `bash /etc/custom_service/start_service.sh &`（L1084-1087）——**首启自定义脚本的官方挂点**；自己的首启逻辑应放进 start_service.sh 模式，而不是另起炉灶改 rc.local。
- banner 写入菜单入口提示（L1233-1234）：`System → Amlogic Service → Install OpenWrt` / `Online Update`。
- `root/.todo_rootfs_resize=yes`：首启自动扩容第 3/4 分区（L1176-1177）。
- btrfs `etc` 子卷快照 `.snapshots/etc-000`（L1275-1277）。
- 默认关闭 hw_flow/sw_flow（turboacc，L1078-1081）、nft-qos 限速（L1093）、openssl 引擎（L1096）。

## 用户侧安装流（documents/README.cn.md）

1. 镜像 `.img.gz` 原样写入 U 盘/TF（gzip 不解包，dd 或 Etcher）。
2. 盒子从 USB 启动——**USB 启动优先于 eMMC**（README.cn.md L671）。
3. LuCI → System → Amlogic Service → Install OpenWrt（L304）。
4. 装前备份：`openwrt-ddbr` → `b` 备份 Android TV 到 `/ddbr/BACKUP-arm-64-emmc.img.gz`，`r` 恢复（L605）。
5. 安装完成拔 U 盘，从 eMMC 重启。

## 命令行等价物（SSH/TTYD）

- `openwrt-install-amlogic`：交互式安装到 eMMC。
- `openwrt-kernel -s` 等：内核救援（documents/README.md L439；无磁盘参数时默认从 U 盘恢复到 eMMC/NVMe/sdX）。
- `openwrt-ddbr`：备份/恢复原生 Android。

## 边界与坑

- **Rockchip 不走该菜单**：`SHOW_INSTALL_MENU='no'`（L1261-1264）；Rockchip 安装方式见 documents/README.md L373（指向 Armbian 手册第 8 章）。别把 Amlogic 的 eMMC 流程答成通用流程。
- 写主线 u-boot 后极少数设备不启动 → TTL 焊 5-10K 上/下拉电阻（README.cn.md L631）。
- eMMC 已有系统导致 U 盘起不来 → 改名 eMMC `/boot/boot.scr` 为 `boot.scr.bak` 强制 U 盘启动（README.cn.md L672）。
- 想改安装器行为 → 上游 ophub/luci-app-amlogic 提 PR；remake 只是搬运工。
- 回答"哪段代码装 eMMC"时不要指到 remake——安装逻辑在 luci-app-amlogic 仓库。

## 破坏性操作契约

写 eMMC 属不可逆破坏性操作：执行前必须复述目标设备/分区并获得显式确认；批量刷写前先留存可回退固件（如 openwrt-ddbr 备份）。契约总纲见 fw-core。
