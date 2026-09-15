---
name: fw-toolchain
license: Apache-2.0
description: "Decide who hosts the cross-toolchain for firmware builds and pin its version across the three toolchain families — OpenWrt userland cross builds (aarch64-unknown-linux-musl pattern: rustup target add + a host cross gcc like gcc-aarch64-linux-gnu on a Linux host/container), ESP-IDF managed toolchains (riscv32-esp-elf / xtensa-esp-elf are installed and activated by the IDF itself via its install/export tooling — never hand-installed via apt/brew), and OpenWrt kernel/host toolchains hosted by buildroot or the pinned-release Image Builder tarball with SOURCE_DATE_EPOCH. Use when users ask 交叉编译/cross compile, 装工具链, aarch64/musl 静态二进制, 找不到 xtensa-esp-elf-gcc, sysroot, or complain toolchain 版本不一致/固件行为因编译机而异. Core stance refuses hand-assembled sysroots and manual ESP toolchain installs — version drift makes artifacts irreproducible. Route ESP-IDF project work to esp32-idf, OpenWrt image building to openwrt-image-build, no-hardware verification to fw-emulation, and release artifacts/checksums to fw-release-gate."
---

# 固件交叉工具链（托管优先与版本锚定）

**核心立场：优先让平台构建系统托管工具链，禁止手工拼 sysroot。** 工具链版本漂移 = 头文件/libc/链接器与目标环境不匹配，产物在设备上行为不可解释且不可复现。三大工具链族各有一位"托管者"，先问"谁托管"，再谈怎么用。

## Determine Task Type

1. **OpenWrt 用户态交叉编译**（如给 aarch64 设备编 Rust/静态小工具）→ Workflow A。
2. **ESP32 工具链**（xtensa-esp-elf / riscv32-esp-elf）→ Workflow B：**不手动装**，IDF 自带工具链管理托管；工程问题移交 `esp32-idf`。
3. **OpenWrt 内核/镜像构建工具链** → buildroot/IB 托管；构建需求整体移交 `openwrt-image-build`。
4. **版本不一致排障 / 可复现构建** → Workflow C + [version-pinning](references/version-pinning.md)。

## Prerequisites / Preflight

```bash
uname -m                                                    # 宿主架构（IB 与交叉工具链官方形态多为 Linux x86_64）
command -v aarch64-linux-gnu-gcc || true                    # 宿主交叉链接器在不在
rustup target list --installed 2>/dev/null | grep aarch64 || true
idf.py --version 2>/dev/null || echo "IDF not in PATH"      # ESP 链路：IDF 托管是否就绪
```

**三版本轴先分清（不要混用）**：

| 版本轴 | 怎么确认 | 决定什么 |
|---|---|---|
| 本机工具链 | 上面的命令实测 | 当前机器能编什么 |
| 项目锁定 | rust-toolchain.toml / dependencies.lock / IB 固定版本 tarball | 项目真实行为与团队一致性 |
| 上游 latest | 官方 release 页（基线日期见 Offline Baseline） | 升级评估参考，**不自动采用** |

## Offline Baseline

- OpenWrt 基线 = **25.12.5**（走读 **2026-09-02**，不自动更新）；IB 官方发布形态为 Linux-x86_64（`.tar.zst`，旧版 `.tar.xz`）。
- ESP-IDF 基线 = **v6.1**（走读 2026-09-02，不自动更新）；工具链由 IDF 发行包的安装/激活工具托管。
- 之后的版本行为变化以官方源为准，不凭记忆断言。

## Contracts（托管契约）

1. **托管矩阵（本 Skill 第一契约）**：每条链路的工具链有唯一托管者——OpenWrt 用户态=宿主交叉工具链 + 语言层 target；ESP32=IDF 自带工具链管理；OpenWrt 内核/镜像=buildroot/IB。逐条见 [hosting-matrix](references/hosting-matrix.md)。
2. **禁止手工拼 sysroot**：手动拼凑"头文件目录 + 任意交叉 gcc + 别处拷来的 libc"就是版本漂移制造机；缺依赖应回到托管者（IB 的 sysroot 由 IB 自己带、IDF 的 libc 由 IDF 带）。
3. **禁止绕过 IDF 手动安装 ESP 工具链**：apt/brew 装的 xtensa/riscv 工具链版本与项目 IDF 不匹配，轻则配置脚本失败，重则产出的镜像行为不可解释。
4. **版本锚定进版本控制**：IDF=`dependencies.lock` + 固定 IDF 检出版本；OpenWrt=固定版本 IB tarball + `SOURCE_DATE_EPOCH`；Rust/musl=固定 `rust-toolchain.toml` + target。详见 [version-pinning](references/version-pinning.md)。
5. 产物架构必须实证（`file` 输出），不凭"编过了就是对的"。

## Capability Boundaries + Hand-off

不做：工程骨架（esp32-idf）、镜像构建本身（openwrt-image-build）、无板验证（fw-emulation）、真机验收（fw-hil-testing）、发布命名/校验和（fw-release-gate）。

| User Intent | Skill |
|---|---|
| ESP-IDF 工程创建/构建/烧写（含工具链激活细节） | `esp32-idf` |
| OpenWrt 镜像构建 / IB 用法 / FILES 注入 | `openwrt-image-build` |
| 编出来的镜像无板先启动验证 | `fw-emulation` |
| 产物真机在环验收 | `fw-hil-testing` |
| 产物命名 / 校验和 / 发布门禁 | `fw-release-gate` |

## Workflow A — 交叉编译 aarch64 静态二进制（OpenWrt 用户态，含 macOS 场景）

1. **定宿主**：模式以 **Linux 宿主**为基准（官方交叉包与 IB 形态均如此）。macOS/Windows 不要在宿主上硬凑——进 **Docker/Linux 容器**执行同一模式（与 IB 的 macOS 用法一致）。
2. **装宿主交叉链接器（Linux 容器/宿主内）**：发行版交叉 gcc 包（如 Ubuntu `apt-get install gcc-aarch64-linux-gnu`）；**不要**为它手搭 sysroot。
3. **加语言层 target**：Rust 项目 `rustup target add aarch64-unknown-linux-musl`，并把 target 与工具链锁进 `rust-toolchain.toml`（模式已在实测项目验证：TinyNAS 实例即以"rustup target + 宿主交叉 gcc"组合出 aarch64 静态二进制——仅作模式引用）。
4. **链接器对接**：在 `.cargo/config.toml` 里给 target 指定 linker（指向第 2 步的交叉 gcc）。注意边界：纯 Rust 依赖走 musl self-contained 链接通常即可；一旦引入 C 依赖，需要与目标 libc 匹配的交叉工具链，链接配置以实测为准（运行时核验）。
5. **产物实证**：

```bash
file target/aarch64-unknown-linux-musl/release/<bin>
# 期望：ELF 64-bit ARM aarch64 ... statically linked
```

6. 静态二进制扔进目标设备跑通才算数：无板 → `fw-emulation`（boot 冒烟/宿主单测）；有板 → `fw-hil-testing`。

## Workflow B — "装 xtensa gcc"请求的纠正（handoff 立场）

用户说"编译 ESP32 提示找不到 xtensa-esp-elf-gcc，apt 装一个吧"——**纠正，不照做**：

1. ESP 工具链由 **ESP-IDF 托管**：随 IDF 发行包用其安装工具一次性装齐（版本与 IDF 严格配套），每个终端经 IDF 的激活脚本（export 一族）进入环境——手动 apt/brew 安装的版本不受 IDF 管控，属版本漂移。
2. 修复路径 = 修复 **IDF 环境本身**：确认 `idf.py --version` 与项目锁定 IDF 一致，重新走 IDF 的安装/激活流程。
3. 工程侧（安装流程、激活、CI 环境）细节移交 `esp32-idf`，本 Skill 不复述其步骤。

## Workflow C — 工具链版本不一致排障

1. 按三版本轴逐轴实测（Preflight 命令），定位哪根轴漂了。
2. 查锚定文件是否入库且被遵守：`rust-toolchain.toml` / `dependencies.lock` / IB 版本 pin / `SOURCE_DATE_EPOCH`（对照 [version-pinning](references/version-pinning.md) 的命令清单）。
3. 修复方向永远是"对齐到项目锁定轴"，不是"大家升到 latest"。
4. 修复后重建产物并 `file`/sha256 比对；产物发布校验 → `fw-release-gate`。

## Validation Gates

1. 三版本轴有书面记录（本机实测值 + 项目锁定文件路径 + 基线日期）。
2. 产物 `file` 输出与目标架构/链接形态一致（aarch64 + statically linked 之类，逐字留档）。
3. 无手工 sysroot 痕迹：构建命令里没有指向临时拼凑的头文件/libc 目录。
4. 团队两台机器按锁定文件构建出 sha256 一致的产物（可复现性抽检）。
5. "能在设备上跑"的结论必须有真机证据（`fw-hil-testing`），否则标 `Build Verification Only`。

## Pitfalls

1. **不要**手工拼 sysroot——缺头文件/缺库回托管者要，不从三个目录东拼西凑。
2. **不要**apt/brew 手动安装 xtensa/riscv ESP 工具链——IDF 托管之外的都是漂移。
3. **不要**混用三版本轴——"我本机是 latest"不能作为项目构建依据。
4. **不要**用不带版本 pin 的 IB 目录——固定版本 tarball + `SOURCE_DATE_EPOCH` 才可复现。
5. **不要**在 macOS 宿主上硬凑 Linux 交叉编译——进 Linux 容器走基准模式。
6. **不要**引用无日期的"最新版本号"——一律带"截至 2026-09-02"并提示运行时核验。

## Official Sources

- [OpenWrt Image Builder 指南](https://openwrt.org/docs/guide-developer/imagebuilder)
- [OpenWrt 官方下载（固定版本 IB tarball）](https://downloads.openwrt.org/)
- [ESP-IDF Get Started（工具链安装与激活）](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/get-started/)
- [rustup 文档（targets 与 toolchain 文件）](https://rust-lang.github.io/rustup/)

## Privacy

本 Skill 只操作本地构建环境与官方下载源，不采集、不上传用户数据或凭据；构建脚本与 CI 配置里不得写入内网源地址、镜像站凭据等敏感信息。
