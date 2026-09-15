# ESP32 链路选择树（routing-esp32）

read-when：任务已判定为 MCU 固件（ESP-IDF 系），需要决定进入哪个专职 Skill。

## 入口判据

```text
用户在哪个阶段？
├── 还没定芯片 → esp32-variants（选型：经典 ESP32 / S2 / S3 / C3 / C6 / H2）
├── 没有 IDF 工程 → esp32-idf（工程骨架、sdkconfig、分区表、构建烧写）
├── 已有工程，写业务逻辑：
│   ├── 并发/任务模型 → esp32-freertos
│   ├── GPIO/I2C/SPI/UART/PWM/ADC → esp32-peripherals
│   ├── Wi-Fi 首次配网 → esp32-wifi-provision
│   ├── 固件升级 → esp32-ota
│   └── 电池供电/续航 → esp32-lowpower
├── 安全合规 → esp32-secureboot（Secure Boot V2 / Flash 加密）
└── 排障 → esp32-debug（coredump/JTAG/GDB/panic 解读）
```

## 横切 Skill（两条链路通用）

| 需求 | Skill | read-when |
|---|---|---|
| 装交叉工具链/版本管理 | `fw-toolchain` | 构建环境缺失或版本不符 |
| 没板子先跑逻辑 | `fw-emulation` | 硬件未到货/QEMU/Wokwi 验证 |
| 上板验收测试 | `fw-hil-testing` | 声称"硬件可用"之前 |
| 发布/命名/校验和 | `fw-release-gate` | 产物交付前 |

## 典型组合

- **量产前**：esp32-secureboot → esp32-ota（AB 分区）→ fw-hil-testing → fw-release-gate。
- **省电设备**：esp32-lowpower → esp32-variants（C 系列通常更优）→ fw-hil-testing（实测电流）。
- **现场排障**：esp32-debug（coredump）→ esp32-ota（热修复通道）。

## Contracts（进入任一 esp32-* 前确认）

- 芯片型号与 revision、模组/开发板型号；
- ESP-IDF 版本（基线以 esp32-idf 内声明为准）；
- 分区表布局与 flash 大小——不确定禁止编造偏移值；
- 烧写通道（USB-Serial/JTAG/外部 probe）与权限。

## Hand-off

| 下一步 | Skill |
|---|---|
| Rust no_std 的 ESP32（esp-hal） | 包外 `rust-skills/rust-embedded`（refuse 并移交） |
| 裸机其他厂商 MCU（STM32/NRF 裸机 C） | 超界：仅给官方文档指引 |
