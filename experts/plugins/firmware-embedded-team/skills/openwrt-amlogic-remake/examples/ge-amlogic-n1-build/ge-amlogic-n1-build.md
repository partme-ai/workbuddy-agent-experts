# GE · N1 镜像构建命令序列（openwrt-amlogic-remake 黄金示例）

**徽章**：`B0 Build Verification Only`（命令文档，需 Linux root 环境验证）

---

## 前置条件

- Linux 主机（x86_64 或 aarch64，需 root 权限）
- 已安装依赖：`sudo apt-get install -y $(cat make-openwrt/scripts/ubuntu2404-make-openwrt-depends)`
- 已有 rootfs.tar.gz（由 openwrt-image-build 的 IB 产出）

## 命令序列

```bash
# 1. 克隆 ophub fork（首次）
git clone https://github.com/ophub/amlogic-s9xxx-openwrt.git
cd amlogic-s9xxx-openwrt

# 2. 放入 rootfs.tar.gz（文件名任意，以 rootfs.tar.gz 结尾）
mkdir -p openwrt-armsr
cp /path/to/openwrt-25.12.5-armsr-armv8-generic-rootfs.tar.gz openwrt-armsr/

# 3. 执行打包（N1 = -b s905d，不是 -b n1）
sudo ./remake -b s905d -k 6.12.y

# 4. 重命名为 TinyNAS 五段式命名
mv openwrt/out/openwrt_amlogic_s905d_*.img.gz \
   openwrt/out/openwrt_tinynas-pro-n1_v1.0.0-stable_$(date +%Y.%m.%d).img.gz

# 5. 校验和
sha256sum openwrt/out/openwrt_tinynas-*.img.gz
```

## 命令参数说明（来源：remake L194 `getopt -o "b:r:u:k:a:p:s:n:"`）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `-b s905d` | 无 | N1 板型 id（不是 `n1`！见 model_database.conf L52） |
| `-k 6.12.y` | stable 最新 | 内核版本（series 自动解析到最新 patch） |
| `-u stable` | `stable` | 内核 tags（stable/flippy/beta） |
| `-a true` | `true` | 自动升级到同系列最新 patch |
| `-s 384+1280` | `384+1280` | 分区大小 boot_MB+root_MB |
| `-n tinynas` | 空 | builder 签名（flippy-openwrt-release 写入） |

## 关键事实（remake 走读 L436-1377）

1. **输入识别**：`ls openwrt-armsr/*rootfs.tar.gz | head -1`——文件名任意
2. **分区**：p1 FAT32 BOOT（384MB 默认）+ p2 btrfs ROOTFS（1280MB 默认），btrfs zstd:6
3. **u-boot**：原厂 `u-boot-2015-phicomm-n1.bin` dd 到镜像头部（offset 512）；主线 `u-boot-n1.bin` 放 bootfs 作 `u-boot.ext`
4. **DTB**：`meson-gxl-s905d-phicomm-n1.dtb`（板型库 L52 FDTFILE 列）
5. **eMMC 安装**：打包期从 `ophub/luci-app-amlogic` 自动注入 `openwrt-install-amlogic`（L551-566）
6. **产物命名**：`openwrt_amlogic_s905d_k6.12.x_YYYY.MM.DD.img.gz`——需手动重命名为五段式

## 踩坑

- **`-b n1` 不存在**：板型 id 是 `s905d`，不是 `n1`
- **macOS 不可直跑**：需要 Linux root（losetup/btrfs/parted），macOS 用 Docker/WSL
- **rootfs 内置 modules 会被删**：`extract_openwrt` 删除 rootfs 自带 `lib/modules/*`，由 `replace_kernel` 注入 ophub 预编译 modules
