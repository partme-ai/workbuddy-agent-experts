---
name: esp32-ota
license: Apache-2.0
description: Design and troubleshoot ESP-IDF OTA firmware update for ESP32 — dual OTA app slots (ota_0/ota_1) + otadata partition prerequisites with a minimal partitions CSV template, the esp_ota_begin/write/end flow, the NEW→PENDING_VERIFY→VALID/INVALID/ABORTED image state machine, CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE semantics (new image must call esp_ota_mark_app_valid_cancel_rollback() or it rolls back on reboot), esp_https_ota with mandatory server certificate verification, and the pre-upgrade decision checklist (version compare, battery/idle window, rollback rehearsal). Use when the user says OTA 升级/远程升级/固件热更新, asks 加双分区可回滚, reports 升级后设备又跑回旧版本/升级失败, or wants an update channel for deployed devices. Do NOT use for offline/USB serial flashing (route esp32-idf), eFuse anti-rollback and signing setup (route esp32-secureboot), or crash triage of a failed image (route esp32-debug).
---

# ESP32 OTA（远程固件升级）

OTA 的可靠性来自**分区机制 + 状态机 + 回滚确认**三件事咬合。本 Skill 给出基线（高置信）事实与顺序，分区分偏移等设备事实一律"读 target 先行"，禁止编造。

## Determine Task Type

1. **给产品加 OTA 能力**：分区布局改造 + 升级代码 + 升级服务器 → Workflow A（主路径）。
2. **升级后设备跑回旧版本**：疑似回滚 → Workflow B（排障，先查 PENDING_VERIFY 未确认）。
3. **升级通道健壮性/决策**：什么时候允许升级、失败怎么办 → 升级决策检查单 + [rollback-checklist](references/rollback-checklist.md)。
4. **没网也要升级 / 离线刷机**：超界 → refusal 路由 `esp32-idf`（见 Hand-off）。

## Prerequisites / Preflight

```bash
idf.py --version            # IDF 版本（基线见下）
idf.py partition-table      # 读 target 实际分区表——任何分区回答的起点
idf.py confserver 2>/dev/null | head -5 || true   # 存在性自检可忽略
```

1. **读 target 先行**：`idf.py partition-table` 的输出是唯一有效的分区事实来源；没有目标板输出前，**拒绝编造分区偏移/大小**。
2. 确认 flash 实际容量（决定 OTA 槽能开多大）。
3. 升级服务器：HTTPS 可达，CA 证书在手（见 Contracts 第 4 条）。

## Offline Baseline

- ESP-IDF 基线 = **v6.1**（截至走读 **2026-09-02**，不自动更新）；分区机制、OTA 状态机、`CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`、esp_https_ota 均引自基线 §4/§5（官方 partition-tables 与 ota 文档，置信度高）。
- 版本之后行为变化以官方 OTA 文档为准，不凭记忆断言。

## Contracts（设备契约）

1. **分区前提（高置信）**：OTA 需要至少两个 OTA app 槽 **ota_0/ota_1 + otadata 分区**；bootloader 按 otadata 的 ota_seq 选槽，otadata 为空则启动 factory。
2. **镜像有效性状态存于 otadata（不在镜像内）**：VALID/UNDEFINED 可启动；INVALID/ABORTED 不启动。
3. **仅 OTA 槽可回滚，factory 不可**——把生产固件放 factory + OTA 槽的组合是常见且被机制支持的做法，但回滚只发生在 OTA 槽之间。
4. **HTTPS 证书**：esp_https_ota 走 HTTPS，固件必须持有服务器 CA 证书（内嵌方式与校验选项以官方 esp_https_ota 文档为准，运行时核验）。**安全立场：服务器证书校验不可关闭**——关闭校验等于把升级通道开放给中间人投毒。
5. 烧写/擦分区是破坏性操作：改动分区表前复述当前布局（Preflight 输出）并获确认。

## 分区前提与最小 CSV 模板

机制 hand-off `esp32-idf`（CSV 字段、Type/SubType 全集），本 Skill 只给 **OTA 最小完整模板**。Offset 列全部留空 = 交由构建自动排布（高置信：Offset 空 = 自动排布；app 64KB 对齐、数据分区 4KB 对齐由构建保证）——**不要手填记忆里的偏移值**：

```csv
# Name,     Type, SubType,  Offset,  Size,     Flags
# 说明：Offset 留空自动排布；各 Size 按实际 flash 容量与 app 体积调整，
#       最终布局以 idf.py partition-table 输出为准（读 target 先行）。
nvs,        data, nvs,      ,        0x4000,
otadata,    data, ota,      ,        0x2000,
phy_init,   data, phy,      ,        0x1000,
factory,    app,  factory,  ,        1M,
ota_0,      app,  ota_0,    ,        1M,
ota_1,      app,  ota_1,    ,        1M,
```

menuconfig 预设可起点：**"Factory app, two OTA definitions"**（对应上表）；"Single factory app, no OTA" 即无 OTA。构建会校验镜像必须放进某个 app 分区——放不下会直接报错，不要靠缩 nvs 硬挤。

## OTA 状态机（核心反陷阱）

```text
写入非活动槽(esp_ota_begin/write/end)
    -> esp_ota_set_boot_partition，镜像记为 NEW
    -> 重启，bootloader 置 PENDING_VERIFY 后启动新镜像
    ├── 应用自检通过 -> esp_ota_mark_app_valid_cancel_rollback() -> VALID（转正）
    ├── 应用自检失败 -> esp_ota_mark_app_invalid_rollback_and_reboot() -> ABORTED 回滚旧版
    └── 新镜像崩溃/看门狗反复重启，从未调用确认 -> 重启即回滚旧版（INVALID）
```

**本技能第一反陷阱**：开启 `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` 后，**新映像必须在应用侧显式调用 `esp_ota_mark_app_valid_cancel_rollback()`**——不调用的后果不是"默认成功"，而是**首次重启就回滚进旧版**。"升级成功后设备又跑回旧版本"的头号原因就是自检确认被遗漏（排障见 Workflow B）。

API 顺序（高置信）：`esp_ota_begin`（大小未知可传 `OTA_SIZE_UNKNOWN`）→ `esp_ota_write`（分块循环）→ `esp_ota_end`（镜像校验）→ `esp_ota_set_boot_partition`；选槽用 `esp_ota_get_next_update_partition()` 轮转。高层封装用 **esp_https_ota**（`esp_https_ota_config_t`，有 `buffer_size`/`bulk_flash_erase` 等调优项）。防回滚（可选）`CONFIG_BOOTLOADER_APP_ANTI_ROLLBACK`：secure_version 烧 eFuse 仅可递增——启用涉及 eFuse 不可逆操作，路由 `esp32-secureboot`。

## Capability Boundaries + Hand-off

| User Intent | Skill |
|---|---|
| 工程骨架/分区表机制基础/USB 串口烧录 | `esp32-idf` |
| 离线设备升级（无网络） | **refusal**：OTA 本质需要网络；离线走 USB 串口烧录 → `esp32-idf` |
| 签名/防回滚 eFuse/加密镜像 | `esp32-secureboot` |
| 真机升级 + 断电回滚验收 | `fw-hil-testing` |
| 升级包命名/校验和/发布流程 | `fw-release-gate` |
| 升级后新镜像崩溃定位 | `esp32-debug`（coredump） |
| 升级前置网络（凭据失效连不上） | `esp32-wifi-provision` |

## Workflow A — 加 OTA 双分区可回滚（主路径）

1. **读 target**：`idf.py partition-table` 记录当前布局；确认有 ota_0/ota_1/otadata，没有则按上面 CSV 模板改（Offset 留空），**拒绝编造偏移**。
2. **menuconfig**：Partition Table 预选 "Factory app, two OTA definitions"；启用 `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`。
3. **实现升级流**：`esp_ota_get_next_update_partition()` 选槽 → `esp_ota_begin/write/end` → `esp_ota_set_boot_partition` → 重启；下载用 esp_https_ota（证书按 Contracts 第 4 条）。
4. **实现自检确认**：新镜像启动后完成业务级自检（外设在、网络在、关键任务起来），通过后立即 `esp_ota_mark_app_valid_cancel_rollback()`；自检失败调 `esp_ota_mark_app_invalid_rollback_and_reboot()`。**不给确认留"下次再说"**。
5. **真机验收**：见 Validation Gates；其中断电回滚验收 → `fw-hil-testing`。
6. 无真机时全部结论标 `Build Verification Only`。

## Workflow B — 升级后设备重启进旧版（排障）

1. 先查状态机缺口：新镜像里是否存在且**必然执行**的 `esp_ota_mark_app_valid_cancel_rollback()`？（自检挂死/任务阻塞会导致确认永不执行。）
2. 确认 menuconfig：`CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE` 是否开启（开启后语义就是"未确认即回滚"，属机制行为非故障）。
3. 读证据：串口启动日志 + `esp32-debug`（coredump/复位原因）定位新镜像是否崩溃在确认之前。
4. 对照 [rollback-checklist](references/rollback-checklist.md) 的验收单重演一遍升级流程。

## 升级决策检查单（允许开始升级的条件）

1. **版本比较**：目标版本新于当前版本；防回滚需求（eFuse secure_version）→ `esp32-secureboot`。
2. **窗口与电量**：电池设备电量高于阈值；业务空闲窗口；升级中不断电（提示用户）。
3. **镜像预算**：新镜像 ≤ OTA 槽大小（读 target 后才知道）。
4. **回滚预案**：确认逻辑已实现并演练过；失败可回旧版（仅 OTA 槽之间）。
5. **通道安全**：HTTPS + 证书校验开启，不从明文 HTTP 拉镜像。
6. 真机验收项 → `fw-hil-testing`；发布产物校验 → `fw-release-gate`。

## Validation Gates

1. 正常升级：新版本号上报，otadata 指向新槽，应用处于 VALID。
2. **回滚验收**：刷入"自检必失败"的测试镜像 → 设备自动回到旧版并可再次升级（在真机执行；无真机 = Pending HIL）。
3. **未确认语义验收**：确认调用被注释掉的情况下，重启后回到旧版——用于证明反陷阱已理解。
4. 断电中断升级：升级中断后设备仍能启动（旧槽未被破坏）。
5. 通道安全：抓包确认 HTTPS；用过期/错误证书的服务器测试被拒绝。

## Pitfalls

1. **不要**开 ROLLBACK 后忘写确认调用——"升级成功又回旧版"的元凶。
2. **不要**编造分区偏移/大小——Offset 留空自动排布，落点以 `idf.py partition-table` 为准。
3. **不要**关闭 esp_https_ota 的服务器证书校验——那条路我不提供。
4. **不要**把"仅 factory 无 OTA 槽"的布局硬讲成支持回滚——回滚只发生在 OTA 槽之间。
5. **不要**承诺"离线设备也能 OTA"——OTA 本质需要网络；离线走 USB 串口烧录（路由 `esp32-idf`）。
6. **不要**在升级循环里无限重试下载——失败要有退避与上限，避免设备卡在"升级风暴"。

## Official Sources

- [ESP-IDF OTA 文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/ota.html)
- [分区表文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/partition-tables.html)
- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/)

## Privacy

升级元数据（设备版本、序列号、升级服务器 URL）与诊断日志可能含设备标识：不采集、不外发；升级服务器凭据/证书私钥按 `fw-release-gate` 治理，不进仓库与日志。
