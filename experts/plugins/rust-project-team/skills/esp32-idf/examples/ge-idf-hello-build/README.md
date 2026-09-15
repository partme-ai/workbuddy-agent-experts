# GE-3 · ESP-IDF v6.1 锁定版本构建（esp32-idf 黄金示例）

**结论徽章**：`B0 — Build Verification Only`（执行日期 2026-09-02，macOS arm64 宿主）
**验证技能**：本技能 Workflow（三版本轴 → set-target → build）与 dated baseline（ESP-IDF v6.1，2026-08-27 发布）
**诚实边界**：仅构建验证——无烧录、无真机上电。flash/monitor 与运行证据按 `fw-hil-testing` 矩阵取证。

## 被测物

| 项 | 值 |
|---|---|
| ESP-IDF | **v6.1**（git shallow clone tag `v6.1`，含 submodules） |
| 目标 | `esp32c3`（RISC-V，macOS arm64 原生工具链支持） |
| 工程 | `examples/get-started/hello_world`（IDF 自带） |
| 前置 | `./install.sh esp32c3`（预编译工具链自动下载）+ `. ./export.sh` |
| 宿主依赖 | cmake / ninja / dfu-util（Homebrew） |

## 证据（evidence.txt + build-full-log.txt）

| 检查点 | 值 |
|---|---|
| 构建完成 | `Project build complete` + esptool v5.4.0 出镜像 |
| 产物 | `hello_world.bin` 126,688 B；`hello_world.elf` 3.1MB；bootloader.bin 21KB |
| sha256 | `fb1975cc…01189f`（完整值见 evidence.txt） |
| 尺寸门禁 | `0x1eee0 bytes … 0xe1120 bytes (88%) free` —— app 检查通过 |
| flash 命令回显 | `idf.py -p PORT flash`（bootloader 0x0 / pt 0x8000 / app 0x10000） |

## 复现

```bash
git clone --depth 1 --recursive -b v6.1 https://github.com/espressif/esp-idf.git
cd esp-idf && ./install.sh esp32c3 && . ./export.sh
cd examples/get-started/hello_world
idf.py set-target esp32c3 && idf.py build
```

## 执行备注

1. macOS arm64 上 esp32c3（RISC-V）工具链原生可用；xtensa 芯片（ESP32/S2/S3）的 Apple Silicon 工具链支持另核（未实测，不在本 GE 范围）。
2. v6.x 为破坏性清理版本（基线已注明 legacy 驱动移除）——hello_world 直接可用，迁移工程参考 `references/v5-to-v6-migration.md`。
3. `install.sh` 与首次 `idf.py build` 共计下载约 1-2GB，构建约 3-5 分钟（M 系列）。
