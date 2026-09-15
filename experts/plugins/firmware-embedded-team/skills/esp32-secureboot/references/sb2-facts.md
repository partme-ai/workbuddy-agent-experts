# SB2 Facts：Secure Boot v2 与 Flash Encryption 事实表（带置信度）

来源：ESP-IDF 基线 §6（官方 secure-boot-v2 [esp32/esp32c3] 与 flash-encryption 文档 + v6.1 release notes，走读 2026-09-02）。引用本表时必须带日期。不自动更新。

## 1. Secure Boot v2 事实

| 事实 | 内容 | 置信度 |
|---|---|---|
| 签名算法 | ESP32（rev 3.0+）与 ESP32-C3 官方页只描述 **RSA-3072（RSA-PSS）** | 高 |
| 公钥入设备形式 | SHA-256 **摘要**烧入 eFuse；私钥永不进设备 | 高 |
| ESP32 摘要位置 | eFuse BLK2 | 高 |
| C3 摘要位置 | BLOCK_KEY0-5 + KEY_PURPOSE=SECURE_BOOT_DIGESTX | 高 |
| 写保护/读保护 | 摘要须**写保护**；**不可读保护**——软件校验需读取，误开读保护无法启动 | 高 |
| 摘要槽数 | ESP32 仅 1 个；C3 最多 3 个 | 高 |
| 密钥撤销 | `KEY_REVOKEX` 撤销，**不可逆**；支持保守/激进撤销策略 | 高 |
| ECDSA SBv2 | 存在于部分芯片（间接证据：v6.1 release notes 因漏洞对 **H2/C5/P4 禁用 ECDSA SBV2**） | 中（归属推断） |
| ED25519 方案 | **UNVERIFIED——禁止写入任何交付物** | — |
| 各芯片最低 IDF 版本 | **UNVERIFIED——禁止写死 vX.Y** | — |

## 2. Flash Encryption 事实

| 事实 | 内容 | 置信度 |
|---|---|---|
| 算法 | AES-256（硬件加密引擎） | 高 |
| 密钥存储 | eFuse block1；烧录后写+读保护，**软件不可读回** | 高 |
| Development 模式 | 明文串口烧录 **≤3 次**（FLASH_CRYPT_CNT 计数） | 高 |
| Release 模式 | 烧保护位后**无法再明文烧录**，新镜像只能经 OTA | 高 |
| 模式选择含义 | Development 便于调试但有明文烧录窗口；Release 锁死后只能 OTA——量产前必须想清楚 | 高（据上述两条推导） |

## 3. 与 OTA 的组合要点

- 目标形态：signed app（SBv2 校验）+ encrypted flash（FE 保护静态内容）。
- FE Release 后唯一升级通道是 OTA；OTA 镜像须为签名镜像。
- 防回滚：`CONFIG_BOOTLOADER_APP_ANTI_ROLLBACK`，secure_version 烧 eFuse **仅可递增**（基线 §5，高置信）——启用即接受"降级需求永久失效"。
- 启用顺序"先 SB 后 FE"标注为官方推荐顺序；逐条步骤以官方 security 文档为准（基线未逐条抓取，运行时核验）。

## 4. 烧录纪律（eFuse 一次性）

1. 任何烧录动作 = 不可逆；先复述"烧什么、烧到哪、后果"并获确认。
2. 开发演练（rehearsal）不烧生产 eFuse：签名流程、FE 开发模式（记账 ≤3 次）、OTA 升级回滚全走一遍。
3. 生产烧录先小批量（≥3 台）验证开机/OTA/回滚，再放量。
4. 具体烧录命令与参数：以官方 security 文档为准（运行时核验），本包不凭记忆提供。

## 5. 芯片差异速记（高频错误点）

- 摘要槽：ESP32=1 个（BLK2）；C3=最多 3 个（BLOCK_KEY0-5）。
- ECDSA SBv2 禁用（v6.1）：H2/C5/P4——涉及这些芯片的安全方案选型先查 v6.1 release notes 与官方页。
- 撤销策略差异（保守/激进）影响升级兼容窗口：C3 多槽设计支持换钥，ESP32 单槽无退路——ESP32 上换钥=换硬件。
