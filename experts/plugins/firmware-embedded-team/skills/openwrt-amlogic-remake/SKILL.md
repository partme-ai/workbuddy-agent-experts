---
name: openwrt-amlogic-remake
license: Apache-2.0
description: Rebuild an OpenWrt armsr/armv8 rootfs.tar.gz into bootable images for Amlogic/Rockchip/Allwinner TV boxes and SBCs using the ophub amlogic-s9xxx-openwrt `remake` pipeline (dual-partition layout, vendor u-boot dd, ophub kernel three-archive replacement, rootfs refactoring, luci-app-amlogic injection). Use when users ask to build images for boxes such as Phicomm N1, pick a board id or an ophub kernel line, pass remake parameters (-b/-k/-u/-a/-p/-s/-n), troubleshoot a failed remake run, or ask how eMMC installation works on Amlogic boxes. Do not build the armsr rootfs itself (hand off to openwrt-image-build), do not hand-run this Linux-root pipeline on macOS (hand off to fw-emulation), and do not fabricate DTB filenames or board rows.
---

# Amlogic 盒子 OpenWrt 镜像重制（ophub remake）

把 OpenWrt 官方 armsr/armv8 `rootfs.tar.gz` 重制为 Amlogic/Rockchip/Allwinner 盒子可启动的多分区镜像。板型、DTB、u-boot 事实一律取自板型数据库与 ophub 内核包；不确定即停，不编造。

## Determine Task Type

1. **重制镜像**：已有 rootfs.tar.gz，要产出 `.img.gz` —— 走 §Workflow。
2. **定制固件内容**（加包/改配置）：用 Image Builder `FILES=` 产出自定义 rootfs.tar.gz 再喂 remake；不改 remake 仓库内的 `make-openwrt/openwrt-files/`（零 commit 纪律，见 Pitfalls）。
3. **板型/内核/eMMC 咨询**：答案必须落到板型库行、内核包或上游文档；读对应 reference 再回答。
4. **构建报错排查**：对照 6 步流水线定位失败阶段，再读 reference。

## Prerequisites / Preflight

逐项运行时核验，缺一即停：

- Linux x86_64/arm64 + **root**：脚本自检 `id -u == 0`（remake L1356）。核验 `uname -m`、`cat /etc/os-release`。
- 工具链齐全：`for c in losetup parted mkfs.vfat mkfs.btrfs btrfs mkfs.ext4 tar curl git sha256sum; do command -v $c; done`（make_image/extract/replace 阶段全程依赖）。
- 磁盘余量：单板单内核需数 GiB；remake 在剩余 ≤3 GiB 时跳过该板构建（L1325-1332），不要在 3 GiB 边缘起跑。
- **macOS/Windows 不可直跑**：依赖 losetup/btrfs/mount，无宿主对应物。路由：容器仿真 `fw-emulation`，或上游 GitHub Actions（action.yml 以 `sudo ./remake` 运行 L114；输入约定 `openwrt/bin/targets/*/*/*rootfs.tar.gz` L12）。
- 输入文件就位：`openwrt-armsr/*rootfs.tar.gz` —— find_openwrt 只认该目录与该通配（remake L56-57、L436-446），放别处等于没放。

## Offline Baseline

- OpenWrt upstream-refs：**25.12.5**（走读 2026-09-02，不自动更新）。
- ophub/amlogic-s9xxx-openwrt：上游 HEAD **`c593d56`**（2026-08-27，走读 2026-09-02）。本文行号均指该版本 `remake` 脚本。
- 内核默认线：`stable_kernel=("6.12.y" "6.18.y")`（L93）；其余线默认值见 references/kernel-lines.md。
- 默认分区：boot 384 MiB / root 1280 MiB（L121-122）。

## Contracts（不确定禁止编造）

- **输入契约**：`openwrt-armsr/*rootfs.tar.gz` 内含 `etc/openwrt_release`；remake 读取 `DISTRIB_SOURCEREPO/SOURCECODE/SOURCEBRANCH` 用于命名与晶晨宝盒下载 tag（L449-465）。
- **板型契约**：board id 只能取自 `model_database.conf` 第 14 列 BOARD。N1 的 board id 是 **`s905d`**，不是 `n1`（conf L52）。FDTFILE/UBOOT_OVERLOAD/MAINLINE_UBOOT/BOOTLOADER_IMG/KERNEL_TAGS/BOOT_CONF 全部以该行为准 —— 详见 references/board-database.md。
- **分区契约（Amlogic）**：头部保留 4 MiB + msdos 表 + p1 FAT32（BOOT）+ p2 btrfs（ROOTFS，`compress=zstd:6`）（L762-766、L801-826、L164）。Rockchip=16 MiB+GPT+ext4 boot；Allwinner=16 MiB+msdos+FAT32（L767-776）。
- **u-boot 契约（Amlogic）**：镜像头部两段 dd（`bs=1 count=444` 与 `bs=512 skip=1 seek=1`，L832-837）；文件优先 MAINLINE_UBOOT、回退 BOOTLOADER_IMG；bootfs 另放整组 overload 文件（L933-941）。
- **内核契约**：ophub 三包 `boot-*.tar.gz` / `dtb-<platform>-*.tar.gz` / `modules-*.tar.gz`，带 sha256sums 则逐文件校验（L952-957、L613-627）。FDTFILE 必须能在 dtb 包内核对到 —— **DTB 文件名、分区偏移不确定即停**。
- **安装契约**：eMMC 安装能力来自打包期注入的 luci-app-amlogic（晶晨宝盒）（L85、L551-566），remake 流程本身不执行 eMMC 安装 —— 详见 references/emmc-install.md。

## Capability Boundaries + Hand-off

不做：从源码编译 OpenWrt rootfs；生成或修改 DTB；macOS 本地构建；开发 eMMC 安装器；真机验收。

| User Intent | Assigned To |
|---|---|
| 构建 armsr rootfs.tar.gz、IB 选包、`FILES=` 注入定制 | `openwrt-image-build` |
| 无 Linux 环境想仿真跑 remake、QEMU 验证镜像 | `fw-emulation` |
| 刷机后串口/首启/HIL 真机验证 | `fw-hil-testing` |

## Workflow

1. **定板型**：在板型库 grep 型号/别名 → 取 BOARD、FDTFILE、BOOT_CONF、KERNEL_TAGS。read-when：用户给的是商品名/别名，或问"这台能不能刷" → read [board-database](references/board-database.md)。
2. **定内核线**：read-when：涉及 `-u`/`-k`/`-a` 参数或"用哪个内核版本" → read [kernel-lines](references/kernel-lines.md)。
3. **组命令**（期望形态）：

   ```bash
   sudo ./remake -b s905d -k 6.12.y
   # -u flippy        换内核 tag 线（自动剥 kernel_ 前缀）
   # -s 512/2560      boot/root 容量（boot≥256、root≥1024，L293-294）
   # -p 192.168.2.1   改默认 LAN IP（正则校验，L247-254）
   # -n <name>        构建者签名（写入 banner 与 release 文件）
   ```

4. **执行**：六步流水线依次执行、任一步失败即 exit 1（loop_make L1335-1340）：
   `make_image → extract_openwrt → replace_kernel → refactor_bootfs → refactor_rootfs → clean_tmp`
5. **收产物**：`openwrt/out/openwrt_[official_]amlogic_s905d_k6.12.y_YYYY.MM.DD.img.gz`（命名规则 L794；pigz 优先、回退 gzip，L1294-1299）。
   - 模式层面：这是"`<源码别名>_<平台>_<板型>_<内核线>_<日期>`"的 release 命名模板；各发布流程可在此模式上扩段使用，模板本身不绑定具体项目。
6. **要改内容**：回到 `openwrt-image-build` 用 IB `FILES=` 重出 rootfs.tar.gz，再喂 remake —— 不要改本仓库 openwrt-files（见 Pitfalls）。

## Validation Gates

按证据强度分层；缺哪层就标哪层，不越级宣布成功：

1. **产物存在**：`ls openwrt/out/*.img.gz`；`gzip -t *.img.gz` 通过；`file` 显示 gzip 数据。
2. **结构抽检**（Linux）：解压后 `fdisk -l` 应见 FAT32 p1 + btrfs p2；`losetup -P` 挂载核对 `/boot/uEnv.txt` 中 dtb 与板型库 FDTFILE 一致、`etc/flippy-openwrt-release` 中 BOARD/KERNEL_VERSION 正确。
3. **真机验收**：U 盘启动 → LuCI 可达 → 晶晨宝盒安装到 eMMC → 重启从 eMMC 引导。只有走到这一步才能宣布"可用"；仅完成 1-2 标注 **Build Verification Only**，缺真机证据标注 **Pending HIL**。
4. **失败路径**：任一步 `error_msg` 即 exit 1；日志最后一段 `(n/6)` 指向失败阶段，按阶段定位（分区/解包/内核/bootfs/rootfs/清理）。

## Pitfalls

- **不要**用 `n1` 当 `-b` 值 —— board id 是板型库第 14 列 `s905d`（conf L52）。
- **不要**编造 DTB 文件名或本地生成 DTB —— FDTFILE 必须能在 ophub dtb 包里核对到（运行时核验），这是反幻觉红线。
- **不要**在 macOS/Windows 直跑 remake —— 依赖 losetup/btrfs，路由 fw-emulation 或 GitHub Actions。
- **不要**改 `make-openwrt/openwrt-files/` 做定制 —— fork 零 commit 纪律：定制经 Image Builder `FILES=` 产出 rootfs.tar.gz 再喂 remake（该模式已在实测仓库验证：tinynas-files README L3 声明其为"经 Image Builder `FILES=` 注入固件、多架构打包共享的单源覆盖层"），否则上游同步必然冲突。
- **不要**自研 eMMC 安装脚本 —— 打包期已注入晶晨宝盒，重复实现会与 openwrt-install-amlogic 冲突。
- **不要**小于 boot 256 MiB / root 1024 MiB（L293-294 直接报错退出）。
- **不要**把 `6.x.y` 当真实版本 —— 实际是 6.1/6.6/6.12/6.18 四条线（conf 头注释 L26-27）。
- **不要**在磁盘剩余 <3 GiB 时开跑 —— 会被静默跳过并误以为成功（L1325-1332）。

## Official Sources

- <https://github.com/ophub/amlogic-s9xxx-openwrt>（remake 脚本、action.yml、documents/）
- <https://github.com/ophub/kernel>（内核 releases：kernel_stable 等 tag）
- <https://github.com/ophub/luci-app-amlogic>（晶晨宝盒：eMMC 安装/在线更新）
- <https://github.com/ophub/amlogic-s9xxx-armbian>（platform-files/different-files 依赖源）
- <https://openwrt.org/toh/>（设备总表，仅用于交叉核对型号别名，不作为 board id 依据）

## Privacy

- 不采集、不外发用户数据；`-n` 签名与日期写入镜像是用户主动提供的信息。
- 排查可能接触用户 rootfs 内 `/etc` 配置（密钥、口令）：仅在本地分析，不复制进技能输出，不上传。
- 默认 LAN IP 192.168.1.1（L115）写入镜像属预期；用户经 `-p` 自定义的内网地址属敏感信息，提醒勿随截图外发。
