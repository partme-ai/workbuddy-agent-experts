# OpenWrt 链路选择树（routing-openwrt）

read-when：任务已判定为 Linux 网关固件（OpenWrt 系），需要决定走哪条产出链路。

## 三级链路总览

```text
用户要什么？
├── A. 官方支持的设备（ToH 在列）上的完整/定制镜像
│      → openwrt-image-build（官方 Image Builder 直出）
├── B. Amlogic/Rockchip/Allwinner 盒子（N1、S905/S912/…）写 eMMC
│      → openwrt-amlogic-remake（ophub 重打包链）
│      └── 若需预装自定义内容：先用 openwrt-image-build 产 rootfs
│          （armsr target 开 TARGZ 出 rootfs.tar.gz），再交 remake
└── C. 设备已在运行，只改配置/脚本/挂载
       → 不构建镜像：openwrt-uci-defaults / openwrt-procd-init /
         openwrt-storage-mount
```

## 判据细节

### 选 A（IB 直出）当且仅当

- 设备在 [OpenWrt Table of Hardware](https://openwrt.org/toh/start) 在列，且官方 release 提供 Image Builder；
- 需要 `PROFILE` + `PACKAGES` + `FILES=` 覆盖即可表达全部定制；
- 产出 sysupgrade/factory 镜像用于官方刷写流程。

### 选 B（ophub 重打包）当

- 目标是 Amlogic/Rockchip/Allwinner 盒子（如 Phicomm N1），设备不在官方 ToH 或官方镜像不含 eMMC 写入布局；
- 消费的是 `openwrt-armsr-armv8-generic-rootfs.tar.gz` 这类通用 rootfs（ophub README：把该文件放入 `openwrt-armsr/` 目录后用其打包脚本制作各 board 镜像；基线 HEAD `c593d56`）；
- 变砖风险与串口救援预期要提前告知用户 → 交接 `openwrt-serial-recovery`。

### 选 C（仅运行时配置）当

- 设备已在跑，且变更可用 UCI/init.d/hotplug 表达；
- 无需增删包、无需改内核/DTB。需要装包而空间不够时升级为 A。

## 链路组合模式

"给 N1 做带自研 Web 和开机自启服务的 NAS 固件"（真实生产模式）：

1. `openwrt-image-build`：armsr target，`PACKAGES=` 预装包，`FILES=` 注入 `/etc/init.d/`、`/etc/uci-defaults/`、`/www/` 覆盖层，开启 rootfs.tar.gz 产物；
2. `openwrt-amlogic-remake`：消费 rootfs.tar.gz，生成盒子 eMMC 镜像；
3. `fw-release-gate`：命名、校验和、发布门禁。

## Hand-off

| 下一步 | Skill |
|---|---|
| 镜像构建细节（IB 下载/FILES 语义/三层包） | `openwrt-image-build` |
| 盒子重打包/写 eMMC | `openwrt-amlogic-remake` |
| 首启配置语义（为什么放 uci-defaults） | `openwrt-uci-defaults` |
| init 脚本规范（rc.common/START=） | `openwrt-procd-init` |
| 构建失败后的串口救援 | `openwrt-serial-recovery` |
| 发布门禁 | `fw-release-gate` |
