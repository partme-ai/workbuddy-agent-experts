---
name: openwrt-image-build
license: Apache-2.0
description: Build customized OpenWrt images with the official Image Builder — download and cache the IB, layer PACKAGES (common/tier/arch), inject a FILES= rootfs overlay with correct semantics, run make image with PROFILE validation, and collect sha256-verified artifacts. Use when users ask to 构建/定制 OpenWrt 镜像, add or pin packages via PACKAGES=, inject custom files/services/web UI via FILES=, use DISABLED_SERVICES or ROOTFS_PARTSIZE, or produce a rootfs.tar.gz for a downstream repack; hand off Amlogic/N1 盒子 eMMC image repacking to openwrt-amlogic-remake, and runtime-only config questions (init scripts, first-boot UCI, mounts) to their dedicated skills.
---

# OpenWrt Image Builder 镜像构建（openwrt-image-build）

用官方 Image Builder（IB）构建定制 OpenWrt 镜像：`PACKAGES=` 选包、`FILES=` 注入覆盖层、`PROFILE=` 定设备、产物带 sha256。所有 FILES= 语义论断来自上游 `include/rootfs.mk` 与 IB `target/imagebuilder/files/Makefile` 走读（基线见 Offline Baseline）。

## Determine Task Type

1. **IB 直出**：官方 ToH 在列设备，用官方 IB 产 sysupgrade/factory 镜像 → 本 Skill。
2. **ophub 重打包**：Amlogic/盒子（N1 等）写 eMMC → 本 Skill 只负责产出 `rootfs.tar.gz`，重打包移交 `openwrt-amlogic-remake`。
3. **仅运行时配置**：设备已在跑，改 UCI/init.d/挂载即可 → 不构建镜像，移交 `openwrt-uci-defaults` / `openwrt-procd-init` / `openwrt-storage-mount`。

## Prerequisites / Preflight

```bash
# 1. 平台：IB 官方发布为 Linux-x86_64；macOS/Windows 用 Docker 内 Linux
uname -m   # 期望 x86_64
make --version >/dev/null && echo make-ok

# 2. 磁盘：IB 解压 + 下载缓存 + 产物，预留 ≥5GB
df -h .

# 3. 工具：.tar.zst 解压需 zstd（OpenWrt 24.10+ 的 IB 是 .tar.zst，旧版 .tar.xz）
command -v curl tar make sha256sum zstd || true

# 4. 下载域可达（IB 运行时按 repositories.conf 拉 ipk）
curl -fsI https://downloads.openwrt.org/releases/ >/dev/null && echo net-ok
```

缺 `zstd` 时：`sudo apt-get install -y zstd`（Ubuntu）。

**Offline Baseline**：OpenWrt **25.12.5**（IB 行为走读上游 `include/rootfs.mk`、`target/imagebuilder/files/Makefile`，日期 2026-09-02，不自动更新）。之后版本的语义变化以官方源为准。

## Mandatory Device Contracts

构建前确认并记录，**不确定禁止编造**：

- 目标设备型号 + OpenWrt `PROFILE` 名——以目标版本 IB 目录下 `make info` 输出为唯一权威。PROFILE 对不上设备就是错镜像；
- OpenWrt 版本与 target 路径（如 `x86/64`、`ramips/mt7621`、`armsr/64`）——下载站路径恒为 `arch/subarch`；
- 产物形态：sysupgrade / factory / combined(-efi) / rootfs.tar.gz（下游用途决定）；
- 若走 ophub 重打包：目标 board 型号由 remake 链确认，本 Skill 不猜。

设备不在 ToH、或 IB 无对应 PROFILE → 停下路由 `openwrt-amlogic-remake` 或查官方 ToH，不要"挑个相近的 PROFILE 试试"。

## Capability Boundaries + Hand-off

边界：本 Skill 只管"官方 IB 构建镜像"这一段；设备端刷写/重打包、运行时配置、发布门禁均不在内：

| 下一步 | Skill |
|---|---|
| 拿 rootfs.tar.gz 重打包盒子 eMMC 镜像（N1/Amlogic） | `openwrt-amlogic-remake` |
| init.d 脚本怎么写（rc.common/START=/STOP=） | `openwrt-procd-init` |
| uci-defaults 首启配置语义与幂等规范 | `openwrt-uci-defaults` |
| 磁盘挂载/USB 存储配置进镜像 | `openwrt-storage-mount` |
| 产物命名/校验和/发布门禁 | `fw-release-gate` |
| 刷写后变砖/串口救援 | `openwrt-serial-recovery` |

## Workflow

### 1. 下载并缓存 Image Builder

```bash
VER=25.12.5; TARGET_PATH=x86/64          # 按实际设备改
BASE="https://downloads.openwrt.org/releases/${VER}/targets/${TARGET_PATH}/openwrt-imagebuilder-${VER}-${TARGET_PATH//\//-}.Linux-x86_64"
mkdir -p ib-cache && cd ib-cache
curl -fsSL --retry 3 -o ib.tar.zst "${BASE}.tar.zst" \
  || { curl -fsSL --retry 3 -o ib.tar.xz "${BASE}.tar.xz"; DECOMP=(-J); }
mkdir -p "openwrt-imagebuilder-${VER}" && tar ${DECOMP:-(--zstd)} -xf ib.tar.* -C "openwrt-imagebuilder-${VER}" --strip-components=1
cd "openwrt-imagebuilder-${VER}"
```

（生产模板 `build-template.sh:72-99`：先试 `.tar.zst`，404 则回退 `.tar.xz`；IB 目录按版本缓存复用。）

### 2. 实证 PROFILE

```bash
make info    # 列出 Current Target / Available Profiles / 每个 Profile 的 Packages
```

期望输出包含目标设备条目；把用户给的设备型号与 `SupportedDevices` 字段对照。找不到即停（见 Contracts）。

### 3. 组装 PACKAGES（三层叠加模式）

生产模板（`build-template.sh:167-176`）把包分三层文本文件，去注释后拼接：

```bash
COMMON_PKGS=$(grep -v '^#' packages.common.txt | tr '\n' ' ')   # 全设备通用
TIER_PKGS=$(grep -v '^#' packages.tier-pro.txt | tr '\n' ' ')   # 档位/场景层
ARCH_PKGS=$(grep -v '^#' arch/packages.txt       | tr '\n' ' ') # 架构专属层
PACKAGES="${COMMON_PKGS} ${TIER_PKGS} ${ARCH_PKGS}"
```

语法（IB Makefile `image` 帮助文本与 `BUILD_PACKAGES` 过滤逻辑，L143-147）：`PACKAGES="pkg-a pkg-b"` 追加；`PACKAGES="-pkg-c"` 从默认集**移除** pkg-c。先 `make manifest` 预演清单再出镜像。

### 4. 准备 FILES= 覆盖层

覆盖层是"按 rootfs 相对路径摆放的目录树"，实际长相（`tinynas-files/`）：

```text
files/
├── etc/init.d/tinynas-boot        # procd 脚本：#!/bin/sh /etc/rc.common + START=
├── etc/uci-defaults/50-tinynas    # 首启幂等配置，末行 exit 0
├── etc/config/samba4              # UCI 配置
├── etc/hotplug.d/block/50-disk    # 热插拔脚本
├── usr/bin/tinynas-machine-id     # 可执行工具
└── www/index.html                 # LuCI 之外的自有页面
```

注入语义（权威依据 `rootfs.mk:71-74` `prepare_rootfs` + `rules.mk:475-488` `file_copy`）——细节逐条见 [files-injection-semantics](references/files-injection-semantics.md)：

- **覆盖式合并，不是整包替换**：`file_copy` 把覆盖层 `cp` 到已装好的 rootfs 上。同路径文件被覆盖；覆盖层没碰的既有文件**原样保留**；
- **先删同名符号链接**：合并前先清除 rootfs 中将被覆盖路径上的符号链接（`rules.mk:480-486`），避免 cp 跟链写穿；
- init.d 脚本**不要手放 `/etc/rc.d/`**：`prepare_rootfs` 对带 `#!/bin/sh /etc/rc.common` shebang 的 `/etc/init.d/*` 自动执行 `enable` 生成启用链接；列进 `DISABLED_SERVICES` 的才被 `disable`（`rootfs.mk:104-113`）；
- 权限位会被保留：init.d/cgi-bin/usr/bin/hotplug.d 下的文件源缺 `+x` 镜像里就缺（`cp -a` 语义）；uci-defaults 由 sh source，不需要 +x。

### 5. 构建与收集

```bash
rm -rf files && mkdir -p files && cp -a /path/to/your-overlay/. files/
make image \
  PROFILE="<profile-from-make-info>" \
  PACKAGES="${PACKAGES}" \
  FILES="$(pwd)/files"
# 可选：BIN_DIR= 输出目录  EXTRA_IMAGE_NAME= 名字后缀
#       DISABLED_SERVICES="svc1 svc2"  ROOTFS_PARTSIZE=<MB>
```

参数如何传递：IB `image` 目标先 `_check_profile` 校验 PROFILE（不存在直接报错退出），再把 `FILES`→`USER_FILES`、`PACKAGES`→`USER_PACKAGES` 传入 `prepare_rootfs`（IB Makefile L354-364、L282）。流程为 package_install（opkg `--offline-root` 装包）→ prepare_rootfs（覆盖层合并 + postinst 重放 + init.d enable）→ build_image → sha256 checksum（L176-187）。

收集与校验（生产模板 `build-template.sh:187-229`）：

```bash
OUT=bin/targets/<arch>/<subarch>
for f in "${OUT}"/*.img.gz "${OUT}"/*-sysupgrade.bin "${OUT}"/*-factory.bin "${OUT}"/*rootfs.tar.gz; do
  [ -f "$f" ] || continue
  cp "$f" dist/ && (cd dist && sha256sum "$(basename "$f")" > "$(basename "$f").sha256")
done
```

产物分类命名建议带 kind 后缀（sysupgrade/factory/combined/combined-efi/rootfs），发布门禁见 `fw-release-gate`。

## Validation Gates

1. `make info` 能列出目标 PROFILE（否则第 2 步就停）；
2. `make manifest PROFILE=... PACKAGES=...` 预演包清单，确认无依赖冲突、无意外移除；
3. `make image` 退出码 0，且**无** `postinst script ... has failed` 行——postinst 重放失败会使构建失败（`rootfs.mk:86-94`）；
4. 产物存在且 `sha256sum -c` 通过；
5. 用 `unsquashfs -l` 或解包 rootfs 抽查：覆盖文件就位、`/etc/rc.d/` 里启用链接由 IB 生成且无手工残留；
6. **构建成功 ≠ 硬件可用**：无真机刷写验证前，一切结论标注 `Build Verification Only`；刷写验证与在环测试移交 `fw-hil-testing`。

## Pitfalls

1. **不要**把 FILES 当"rootfs 整包替换"——它是覆盖式合并；试图用一个精简 files/ 目录"缩rootfs"不会删掉任何既有文件。
2. **不要**在覆盖层手放 `/etc/rc.d/Sxx*` 链接——IB 会按 init.d + rc.common 自动 enable 重造，手放是冗余且会被 lint 门禁拒绝（生产模板 `build-template.sh:155-157` 明确禁止）。
3. **不要**假设"给 IB 喂 rootfs.tar.gz 就能出镜像"——官方 IB 的输入是 `repositories.conf` 提供的 **ipk**（`opkg --offline-root` 装包，IB Makefile L93-97）；rootfs.tar.gz 只是 target 开启 `CONFIG_TARGET_ROOTFS_TARGZ` 时的**产物**（`image.mk:372-376`），ophub 重打包消费的是 armsr 的 `armv8 generic rootfs.tar.gz`（ophub README，基线 `c593d56`）。
4. **不要**编造 PROFILE/设备兼容名——只认 `make info`。
5. **不要**忽略覆盖层权限位与脚本规范：init.d 缺 `rc.common` shebang 或 `START=`、uci-defaults 末行缺 `exit 0` 都会被门禁拦下（`build-template.sh:148-165`）。
6. **不要**在 rootfs.tar.gz 之外还想让 IB 直接产出盒子 eMMC 镜像——那是 remake 链的活。

## On-Demand Resources

- [files-injection-semantics](references/files-injection-semantics.md)：FILES=/prepare_rootfs 逐条语义，读于设计覆盖层或排查"文件没进去/服务没自启"。
- [packages-layering](references/packages-layering.md)：三层包叠加与 `-pkg` 移除，读于组织大型 PACKAGES 列表。
- [reproducible-build](references/reproducible-build.md)：SOURCE_DATE_EPOCH 与可复现构建，读于 CI 产出可校验镜像。

## Official Sources

- [Image Builder 使用指南](https://openwrt.org/docs/guide-developer/imagebuilder)
- [OpenWrt 官方下载（IB 与镜像）](https://downloads.openwrt.org/)
- [OpenWrt Table of Hardware](https://openwrt.org/toh/start)
- [upstream include/rootfs.mk](https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob;f=include/rootfs.mk)
- [upstream target/imagebuilder files/Makefile](https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob;f=target/imagebuilder/files/Makefile)

## Privacy

本 Skill 只操作本地构建环境与官方下载源，不采集、不上传用户数据或凭据；不要把私有签名密钥、许可证文件放进将被分享的覆盖层。
