# QEMU OpenWrt Boot Smoke — 启动冒烟手册

> 基线：OpenWrt 25.12.5（走读 2026-09-02，不自动更新）。**镜像文件名与下载路径以当版官方下载站目录为准**，不凭记忆背。

## 1. 拿镜像

| 来源 | 路径 | 说明 |
|---|---|---|
| 官方下载 | `https://downloads.openwrt.org/releases/<VER>/targets/armsr/armv8/` | 取 combined-efi 的 `.img.gz`；**文件名以下载站当版目录为准** |
| 自建产物 | `bin/targets/armsr/armv8/*combined-efi*.img.gz` | 由 `openwrt-image-build`（IB `make image`）产出 |
| x86/64 | 官方下载或自建的 `x86/64` combined / combined-efi | BIOS 引导用 combined；EFI 引导需 OVMF 固件 |

N1 等盒子的可刷写镜像不是这份 armsr 直出镜像（那是 remake 链的产物）；但 armsr 镜像与盒子镜像同源（remake 消费 armsr rootfs），**boot 冒烟验证的是"镜像能引导、用户态活着"这一层**，布局差异不归本 Skill 证。

## 2. armsr/armv8 启动（基准流程）

```bash
gunzip -k openwrt-<VER>-armsr-armv8-generic-ext4-combined-efi.img.gz   # 文件名以实际下载为准
qemu-system-aarch64 -M virt -cpu cortex-a57 -m 512M -nographic \
  -bios /path/to/QEMU_EFI.fd \
  -drive file=openwrt-<VER>-armsr-armv8-generic-ext4-combined-efi.img,format=raw,if=none,id=hd0 \
  -device virtio-blk-device,drive=hd0
```

- `-M virt` + UEFI 固件是 armsr EFI 镜像的引导前提；`QEMU_EFI.fd` 来自 edk2（发行包/brew 名各异，**运行时核验本机路径**）。
- `-nographic` 把串口接到当前终端；参数细节以 QEMU virt 机型官方文档为准（运行时核验）。
- 退出 QEMU：`Ctrl-A` 然后按 `x`。

## 3. x86/64 一行版

```bash
qemu-system-x86_64 -nographic -drive file=<combined>.img,format=raw
# combined-efi 镜像需加 OVMF：-bios /path/to/OVMF.fd（路径运行时核验）
```

## 4. 冒烟判据与汇报口径

1. 串口出现 OpenWrt boot log（内核解压/启动横幅）。
2. 走到 OpenWrt shell 提示符；执行 `uname -a` 等基础命令有响应。
3. boot log 全程存档为证据。
4. 汇报模板：**"Boot Verification Only：镜像 `<文件名>` 在 QEMU（virt/AArch64，UEFI）引导至 shell"**；下一步真机验收 → `fw-hil-testing`。

## 5. 覆盖边界（问什么答"不一致"）

| 真机维度 | QEMU 覆盖？ | 结论口径 |
|---|---|---|
| 能否引导、用户态起得来 | 是 | Boot Verification Only |
| 无线（Wi-Fi 驱动/吞吐/射频） | **否** | 不一致 → `fw-hil-testing` |
| 以太网 PHY/交换芯片行为与吞吐 | **否**（virtio 网卡仅是体系结构层模型） | 不一致 → HIL |
| eMMC/存储控制器时序 | **否**（virtio-blk 是理想块设备） | 不一致 → HIL |
| DTB/引脚/外设树行为 | **否**（设备树按机型，virt 不等于你的板子） | 不一致 → HIL |

## 6. ESP32（诚实边界）

QEMU 对 ESP32 系列的支持有限（芯片/外设覆盖不完整），本包**未验证**，能力描述一律 `Pending verification`；上游指针：espressif/qemu 分支（自行核验）。无板替代：宿主级逻辑测试（见 [host-mocking](host-mocking.md)）或托管仿真器（如 Wokwi，能力边界以官方文档为准——运行时核验）。外设/真机行为 → `fw-hil-testing`。

## 7. 常见失败

| 症状 | 排查 |
|---|---|
| 串口无任何输出 | 固件路径错/未给 `-bios`；镜像忘了解压（直接喂了 .img.gz） |
| UEFI 卡在固件菜单 | 镜像不是 combined-efi 或块设备没挂上（drive/device 参数） |
| 内核 panic 找不到 root | 镜像与机型不匹配（如把非 EFI 镜像喂 EFI 流程）；换基准组合重试 |
| `qemu-system-aarch64: command not found` | 安装 QEMU（macOS: `brew install qemu`），或换 Linux 容器 |
