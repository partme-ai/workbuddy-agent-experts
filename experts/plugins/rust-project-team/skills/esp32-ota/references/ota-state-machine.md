# OTA State Machine：otadata 状态与 API 顺序

来源：ESP-IDF 基线 §4/§5（官方 partition-tables 与 ota 文档，走读 2026-09-02，置信度高）。不自动更新。

## 1. 分区机制事实

- OTA 前提：至少两个 OTA app 槽 `ota_0`/`ota_1`（SubType 0x10~0x1F 对应 ota_0~ota_15）+ `otadata` 分区。
- bootloader 按 otadata 里的 **ota_seq** 选择启动槽；otadata 为空 → 启动 factory。
- `esp_ota_get_next_update_partition()` 按 ota_seq 轮转选"非活动槽"作为写入目标。
- **镜像有效性状态存于 otadata，不在镜像内**。
- menuconfig 预设："Single factory app, no OTA" / "Factory app, two OTA definitions"。
- 构建期校验：镜像必须能放进某个 app 分区；app 分区 64KB 对齐、数据分区 4KB 对齐、Offset 空 = 自动排布。

## 2. 镜像状态机（otadata 视角）

```text
                    esp_ota_set_boot_partition
  [写入非活动槽] ──────────────────────────────► NEW
                                                   │ 重启
                                                   ▼
                                           PENDING_VERIFY（仅当
                                           CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE）
                                           bootloader 先启动它，等待应用确认
                             ┌─────────────────┼──────────────────┐
        esp_ota_mark_app_    │                 │                  │ 应用从未确认
        valid_cancel_rollback│                 │ esp_ota_mark_app_ （崩溃/看门狗/掉电）
                             ▼                 ▼ invalid_rollback_ ▼
                          VALID             ABORTED ──► 重启回滚   INVALID ──► 重启回滚
                     （转正，正常运行）    （显式判死+回滚）          （未确认判死+回滚）
```

- 可启动状态：VALID / UNDEFINED；不可启动：INVALID / ABORTED。
- **未开启 ROLLBACK_ENABLE 时没有 PENDING_VERIFY**：新镜像首启即视为可用——也就没有"自动回滚"这层保护，二选一要清醒。

## 3. 原生 API 顺序（高置信）

1. `esp_ota_get_state_partition()` / 读 otadata：先弄清当前槽与新槽状态（排障第一步）。
2. `esp_ota_begin(partition, size, handle)`：size 已知传实际值，未知传 `OTA_SIZE_UNKNOWN`。
3. `esp_ota_write(handle, data, offset, size)`：分块循环写下载流。
4. `esp_ota_end(handle)`：镜像完整性校验——失败必须清理句柄并放弃本次升级。
5. `esp_ota_set_boot_partition(partition)`：改 otadata，重启后生效。
6. 新镜像首启：业务自检 → `esp_ota_mark_app_valid_cancel_rollback()` 转正；失败 `esp_ota_mark_app_invalid_rollback_and_reboot()` 回滚。

## 4. 高层封装 esp_https_ota

- `esp_https_ota_config_t` 配置 URL/证书等；调优项含 `buffer_size`、`bulk_flash_erase` 等（以官方头文件/文档为准，运行时核验具体字段）。
- 证书：固件须持有升级服务器 CA；**服务器证书校验不可关闭**（安全立场，见 SKILL.md Contracts）。
- 封装内部同样遵循上面的状态机——封装不替代"应用自检 + 确认调用"。

## 5. 防回滚（可选，涉及 eFuse）

- `CONFIG_BOOTLOADER_APP_ANTI_ROLLBACK`：secure_version 存 eFuse，**仅可递增**（不可逆）。
- 启用前必须先解决：版本号管理、降级测试需求、eFuse 不可逆后果评估 → 路由 `esp32-secureboot`。

## 6. factory 与回滚的边界

- 回滚只发生在 OTA 槽之间（NEW/PENDING_VERIFY 的槽 ↔ 上一个 VALID 槽）。
- factory 槽无回滚语义；"factory 出厂 + ota 槽升级"是受支持的布局，但不要把 factory 当作 OTA 回滚目标讲述。
