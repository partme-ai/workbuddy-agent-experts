# menuconfig 决策点（menuconfig-decisions）

read-when：执行 `idf.py menuconfig` 前后，需要决定改哪些配置项。
基线：ESP-IDF v6.1，走读 2026-09-02。Kconfig 名称以基线高置信项为准；其余以本机 menuconfig 搜索结果为准。

## 核验先行

```bash
grep -E "CONFIG_(FREERTOS|BOOTLOADER_APP|ESP_COREDUMP|IDF_TARGET)" sdkconfig
```

先看现状再改；menuconfig 内用其搜索功能定位条目，不要凭记忆手改 sdkconfig 行。

## 决策表

| 决策点 | 配置项 | 基线事实 |
|---|---|---|
| 分区表布局 | Partition Table 预设 | 预设二选一："Single factory app, no OTA" / "Factory app, two OTA definitions"；自定义则指向项目内 CSV |
| OTA 回滚 | `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` | 开启后新 app 首启为 PENDING_VERIFY，应用须自检后调 `esp_ota_mark_app_valid_cancel_rollback()` 或 `esp_ota_mark_app_invalid_rollback_and_reboot()`；仅 OTA 槽可回滚，factory 不可 |
| OTA 防降级 | `CONFIG_BOOTLOADER_APP_ANTI_ROLLBACK` | secure_version 烧 eFuse，只可递增；与 Secure Boot 组合使用，评估留足升级余量 |
| coredump 目的地 | `CONFIG_ESP_COREDUMP_TO_FLASH_OR_UART` | panic 时保存到 flash（data/coredump 分区）或 UART；分析走 `idf.py coredump-info` / `coredump-debug` |
| 核数 | `CONFIG_FREERTOS_UNICORE` | S2/C3 等单核芯片恒为 unicore；双核芯片此项决定是否只用单核 |
| FreeRTOS 优先级上限 | `CONFIG_FREERTOS_MAX_PRIORITIES` | 默认 25（有效 0–24，数字越大越高，idle=0）；**可配，运行时以本项目 sdkconfig 为准** |
| 运行时 GDB stub | `CONFIG_ESP_SYSTEM_GDBSTUB_RUNTIME` | 无 JTAG 时的串口调试通道（官方 JTAG 页提及）；专用文档页 UNVERIFIED，用官方搜索核验 |

## 决策原则

1. 一个决策点一次提交：分区表、回滚、coredump 分开改，便于 diff 与回退。
2. OTA 相关两项（回滚/防降级）必须与分区表（双 OTA 槽 + otadata）配套，单独开 Kconfig 而没有分区支撑是无效配置。
3. 优先级默认值引用时必须带"默认 25，可配，以 sdkconfig 为准"，不得写成固定常量。
4. 改完 menuconfig 后 `idf.py build` 重验；sdkconfig 是生成物衍生物，冲突时以重新配置为准。
