---
name: fw-emulation
license: Apache-2.0
description: "\"Verify firmware without hardware at two honest levels — host-level unit tests with mocked device boundaries (OpenWrt userland scripts driven through env-var fixture injection, e.g. the TINYNAS_* fixture pattern; ESP-IDF logic tested via a HAL abstraction with self-mocks, mock component existence to be runtime-verified), and system-level boot smoke under QEMU (OpenWrt armsr/armv8 or x86/64 image booted from the official combined-efi download path; ESP32 QEMU support is limited and stays marked Pending verification). Use when users say 没有板子先验证, 无板测试, QEMU 跑镜像/启动冒烟, 宿主单测/模拟测试, or want to boot-test an OpenWrt image before flashing a box like N1. Completion honesty: emulation passing is Build/Boot Verification Only, never hardware usability; questions about hardware-real behavior (Wi-Fi/eth throughput, RF, timing, eMMC) are answered 不一致 and route to fw-hil-testing. Do NOT use for flashing/on-device acceptance (fw-hil-testing), building images themselves (openwrt-image-build)"
---

# 无板仿真与宿主级验证（fw-emulation）

两级无板验证，证据强度不同、能宣称的结论也不同：**宿主级单测**证逻辑，**系统级 QEMU 启动冒烟**证"镜像能起"。两级都不证硬件行为——模拟通过 = **Build/Boot Verification Only**，不等于硬件可用。

## Determine Task Type

1. **没有板子，先验证 OpenWrt 镜像能不能起** → Workflow A（QEMU boot 冒烟），细节读 [qemu-openwrt](references/qemu-openwrt.md)。
2. **没有设备，先验证业务逻辑**（OpenWrt 用户态脚本 / ESP32 固件逻辑层）→ Workflow B（宿主级 mock），细节读 [host-mocking](references/host-mocking.md)。
3. **"QEMU 里 Wi-Fi/eth 行为和真机一致吗"** → refusal 立场：**不一致**；外设级问题路由 `fw-hil-testing`。
4. **ESP32 无板仿真** → 诚实边界（见 Contracts 第 4 条）：宿主级逻辑测试可做，外设级仿真不做承诺。

## Prerequisites / Preflight

```bash
command -v qemu-system-aarch64 qemu-system-x86_64 || true   # QEMU 在不在（macOS 可 brew 安装）
command -v gunzip file || true
ls <your-image>.img.gz 2>/dev/null                          # 待验证镜像（官方下载或自建产物）
```

1. 待验证镜像来源二选一：官方下载站当版 `combined-efi` 镜像，或自己用 IB 构建的产物（`bin/targets/armsr/armv8/` 下）。
2. UEFI 固件文件（edk2 的 `QEMU_EFI.fd` 一族）按发行/安装方式定位——**路径因平台而异，运行时核验**。
3. 确认"要证什么"：起得来（本 Skill）≠ 配置对（uci 语义属运行时配置技能）≠ 硬件可用（HIL）。

## Offline Baseline

- OpenWrt 基线 = **25.12.5**（走读 **2026-09-02**，不自动更新）；镜像下载路径以**当版官方下载站目录为准**，不凭记忆背文件名。
- ESP32 的 QEMU 仿真能力本包**未验证**：一律标 `Pending verification`，不描述其能力细节。
- 之后的版本行为变化以官方源为准，不凭记忆断言。

## Contracts（完成诚实性契约）

1. **证据分层**：宿主单测 < 系统级 boot 冒烟 < 真机 HIL。汇报必须带层级标注，不得越级宣称。
2. **模拟通过 = Build/Boot Verification Only**：QEMU 里跑到 shell 提示符只证明镜像可引导、基本用户态活着；禁止表述为"可以在真机上用了"。
3. **外设行为不在模拟范围**：QEMU 模拟的是 CPU/内存/块设备等体系结构层；无线、以太网 PHY/交换、射频、时序、eMMC 不被真实模拟——外设问题一律 HIL。
4. **ESP32 QEMU 支持有限**（芯片/外设覆盖不完整）：本包标 `Pending verification`；真机行为验收路由 `fw-hil-testing`。宿主级替代路径见 [host-mocking](references/host-mocking.md)。
5. fixture/golden 数据**独立生成**，不从被测实现复制（否则测试只会复读实现，测不出错）。

## Capability Boundaries + Hand-off

不做：镜像构建（`openwrt-image-build`）、Linux-root 重制流水线本身（macOS 不可直跑 remake——环境约束路由 `openwrt-amlogic-remake`）、刷写与真机验收（`fw-hil-testing`）、发布产物门禁（`fw-release-gate`）。

| User Intent | Skill |
|---|---|
| 构建/定制 OpenWrt 镜像、出 combined-efi 产物 | `openwrt-image-build` |
| 盒子（N1/Amlogic）重制流水线与其运行环境约束 | `openwrt-amlogic-remake` |
| QEMU 冒烟通过后的真机验收（Wi-Fi/eth/eMMC/长跑） | `fw-hil-testing` |
| 交叉工具链托管与版本锚定 | `fw-toolchain` |
| 产物命名/校验和/发布流程 | `fw-release-gate` |

## Workflow A — OpenWrt 镜像 QEMU 启动冒烟（无 N1 先验镜像）

1. **拿镜像**：官方下载站 `releases/<版本>/targets/armsr/armv8/` 下的 combined-efi 镜像（**文件名以当版下载站目录为准**），或自建产物 `bin/targets/armsr/armv8/*combined-efi*.img.gz`。
2. **解压**：`gunzip -k <image>.img.gz` 得 `.img`。
3. **定位 UEFI 固件**：edk2 `QEMU_EFI.fd`（安装路径随平台不同，运行时核验）。
4. **启动**（armsr/armv8 基准形态，参数语义详见 [qemu-openwrt](references/qemu-openwrt.md)）：

```bash
qemu-system-aarch64 -M virt -cpu cortex-a57 -m 512M -nographic \
  -bios /path/to/QEMU_EFI.fd \
  -drive file=<image>.img,format=raw,if=none,id=hd0 \
  -device virtio-blk-device,drive=hd0
```

5. **冒烟判据**：串口输出 OpenWrt boot log 直到 shell 提示符；能在提示符下执行基础命令（如 `uname -a`）。把 boot log 存档为证据。
6. **汇报口径**：写"Boot Verification Only：镜像在 QEMU (virt/AArch64) 可引导至 shell"；Wi-Fi/eth/eMMC/性能等真机问题 → `fw-hil-testing`。
7. x86/64 镜像的一行版与常见失败排查见 [qemu-openwrt](references/qemu-openwrt.md)。

## Workflow B — 宿主级单测（逻辑层 mock）

**OpenWrt 用户态脚本（env-var fixture 注入模式）**：

1. 让被测脚本支持"根路径/数据源环境变量覆盖"（模式即实测项目中的 `TINYNAS_SYSINFO_ROOT` / `TINYNAS_SHARE_ROOT` 一类前缀变量——仅作模式引用，真实例 `tests/run-lint.sh` + `test-machine-id.sh`）。
2. 测试脚本向 fixture 目录注入假数据源，运行被测脚本，断言输出：golden 期望值**独立生成**（注明生成日期与算法）、格式断言、外加负向用例（路径穿越/坏输入必须被拒）。
3. 静态门禁并列进同一入口：`sh -n` 全量语法、uci-defaults 末行 `exit 0`、禁手放 `/etc/rc.d/` 等项目军规。
4. 细节与骨架模板 → [host-mocking](references/host-mocking.md)。

**ESP32 固件逻辑层**：

1. 把业务逻辑编成**宿主可编译单元**：抽象 HAL 接口，测试注入自写 mock；外设时序不在断言范围。
2. 组件注册表中存在 esp-idf mock 类组件（以 "mock" 关键词检索 components registry；**存在性与维护状态运行时核验**）——找到且可用才用，找不到就走自 mock，不等待不臆测。
3. 宿主测试全绿仍只证逻辑；上板行为 → `fw-hil-testing`。

## Validation Gates

1. Workflow A：boot log 存档含"引导至 shell 提示符"证据；汇报带 **Boot Verification Only** 标注。
2. Workflow B：宿主测试入口全绿退出 0；负向用例（穿越/坏输入）至少 1 条且通过；golden 值注明独立生成方式。
3. 每个结论自查三连：证的哪一层？缺哪一层？缺的层路由给谁（HIL / 运行时配置技能）？
4. 无真机证据的最终结论一律补 `Pending HIL`。

## Pitfalls

1. **不要**把 QEMU 跑通汇报成"镜像在设备上可用"——那是 HIL 的结论，不是本 Skill 的。
2. **不要**用 QEMU 验证/评估 Wi-Fi、eth 吞吐、射频、时序、eMMC 行为——模拟器不覆盖，答案是不一致。
3. **不要**背官方镜像文件名——以下载站当版目录为准（基线日期 2026-09-02 之后可能变）。
4. **不要**让宿主断言复制实现逻辑（golden 值要独立生成），否则测试永远绿、永远没用。
5. **不要**为 ESP32 承诺外设级仿真——支持有限，标 `Pending verification`，真机走 HIL。
6. **不要**把 fixture 注入变量硬编码进被测脚本的生产路径——默认行为必须与真机一致，注入只用于测试。

## Official Sources

- [QEMU System Emulation（virt 机型等）](https://www.qemu.org/docs/master/system/)
- [OpenWrt 官方下载（targets/armsr 等）](https://downloads.openwrt.org/)
- [OpenWrt x86/armsr 相关文档](https://openwrt.org/docs/start)
- [edk2 (OVMF/QEMU_EFI)](https://github.com/tianocore/edk2)
- [Espressif QEMU 分支（能力边界自行核验，本包未验证）](https://github.com/espressif/qemu)

## Privacy

本 Skill 只操作本地镜像、本地 QEMU 与本地测试数据，不采集、不外发用户数据；fixture 里不得放真实密钥/口令/设备序列号，用显式构造的假数据；访问官方链接遵守用户环境网络策略。
