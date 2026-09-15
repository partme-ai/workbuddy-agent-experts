# GE-1 · OpenWrt armsr QEMU 启动冒烟（fw-emulation 黄金示例）

**结论徽章**：`B1 — Boot Verified (QEMU)`（执行日期 2026-09-02）
**验证技能**：本技能（fw-emulation）Workflow 的系统级模拟两级中的第②级
**诚实边界**：QEMU 验证的是"镜像能完整启动到网络栈就绪"；Wi-Fi/真实网卡/存储行为与真机**不一致**（见 SKILL.md QEMU 覆盖边界表），硬件验收路由 `fw-hil-testing`。

## 被测物

| 项 | 值 |
|---|---|
| 镜像 | `openwrt-25.12.5-armsr-armv8-generic-ext4-combined-efi.img.gz`（官方下载站） |
| 完整性 | sha256 对照官方 `sha256sums` → OK |
| 运行环境 | Docker Desktop (macOS) 内 `ubuntu:24.04` + `qemu-system-aarch64 8.2.2` + `qemu-efi-aarch64`（QEMU_EFI.fd） |
| QEMU 参数 | `-M virt -cpu cortex-a57 -m 1024 -nographic -bios QEMU_EFI.fd -drive if=none,file=<img>,format=raw,id=hd0 -device nvme,drive=hd0,serial=nvme0 -netdev user,id=n0 -device virtio-net-pci,netdev=n0` |

## 证据（见 boot-log.txt，31KB 完整捕获）

| 检查点 | 日志证据 |
|---|---|
| GRUB 菜单出现 `*OpenWrt` | boot-log.txt L13 区域 |
| EFI 存根加载内核 | `EFI stub: Booting Linux Kernel...` |
| 内核启动 | `[ 0.000000] Booting Linux on physical CPU 0x...` |
| **网络栈就绪（完整启动标志）** | `br-lan: port 1(eth0) entered forwarding state`（t≈40s） |
| 终止方式 | 容器内 `timeout 240` 到点 SIGTERM（预期，非崩溃） |

## 复现

```bash
# 宿主仅需 Docker；文件预置于 /tmp/ge1（镜像下载+sha256 校验）
docker run --rm -v /tmp/ge1:/work -w /work ubuntu:24.04 bash -c "
  apt-get update && apt-get install -y qemu-system-arm qemu-efi-aarch64 coreutils
  timeout 240 qemu-system-aarch64 -M virt -cpu cortex-a57 -m 1024 -nographic \
    -bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd \
    -drive if=none,file=<img>,format=raw,id=hd0 -device nvme,drive=hd0,serial=nvme0 \
    -netdev user,id=n0 -device virtio-net-pci,netdev=n0"
```

## 执行备注（踩坑记录，供技能演进）

1. apt 安装与 QEMU 启动必须在**同一个** `docker run` 内（每次 run 都是新容器）。
2. 宿主 macOS 无 `timeout`——限时控制放容器内 coreutils。
