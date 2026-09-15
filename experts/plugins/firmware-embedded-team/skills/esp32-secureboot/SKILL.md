---
name: esp32-secureboot
license: Apache-2.0
description: Plan and rehearse ESP32 Secure Boot v2 and Flash Encryption for production ESP32 firmware — SBv2 facts (RSA-3072 public-key digest burned into eFuse, write-protected but not read-protected, private key never on device), one-shot eFuse nature requiring a development-stage rehearsal before production burning, Flash Encryption (AES-256, ≤3 plaintext development flashes, irreversible Release mode), the signed-app + encrypted-flash combination with OTA, and key governance (生产密钥绝不进仓库/CI 明文). Use when the user says 安全启动/Secure Boot/固件签名/Flash 加密/量产安全, asks 量产前安全怎么启用, or mentions secure boot keys, eFuse 烧录, or signing keys in CI. Refuses to put signing keys into git/CI and does not assert ED25519 or per-chip minimum IDF versions (UNVERIFIED). For OTA rollback enablement route esp32-ota; for release naming/checksum gating route fw-release-gate.
---

# ESP32 Secure Boot v2 与 Flash Encryption

安全启动与加密的每一步都碰 **eFuse——一次性、不可逆**。本 Skill 的原则：先演练（rehearsal）、后烧录；密钥治理先于技术实施；基线没抓到的事实（如 ED25519）**禁止写入**。

## Determine Task Type

1. **量产前安全方案启用**：SB v2 + Flash Encryption 的启用顺序与演练 → Workflow（决策型主路径）。
2. **密钥治理**：签名密钥怎么生成、存哪、CI 怎么用 → [key-governance](references/key-governance.md)（"key 提交进 git"类请求直接 refusal）。
3. **技术事实核对**：SBv2 算法/eFuse 行为/FE 次数限制 → [sb2-facts](references/sb2-facts.md)。
4. **与 OTA 组合**：signed app + encrypted flash 下的升级通道 → 见"与 OTA 的关系"，实现细节路由 `esp32-ota`。

## Prerequisites / Preflight

```bash
idf.py --version
```

1. **芯片型号 + revision**：ESP32 经典款需 **rev 3.0+** 才支持 SBv2（基线高置信）；C3 官方页描述 RSA-3072。型号不明先停。
2. **是否已有 OTA**：FE Release 模式下新镜像只能经 OTA 进设备——没有 OTA 通道就启用 Release 加密 = 自断后路。
3. **烧录/efuse 工具可用性**：具体烧录命令与工具链（espsecure 等）以官方 security 文档为准（运行时核验），本 Skill 不凭记忆给参数。
4. **密钥现状**：已有签名密钥？在谁手里？有没有进过 git？（进过 = 按已泄露处理，见 key-governance。）

## Offline Baseline

- ESP-IDF 基线 = **v6.1**（截至走读 **2026-09-02**，不自动更新）；SBv2/FE 事实引自基线 §6（官方 secure-boot-v2 与 flash-encryption 文档，置信度高）。
- **ED25519 Secure Boot 方案归属：UNVERIFIED——本 Skill 与其下游一律不写**。
- ECDSA SBv2 归属为中置信：仅可表述为"存在于部分芯片；v6.1 因漏洞对 H2/C5/P4 禁用 ECDSA SBV2"，细节见 [sb2-facts](references/sb2-facts.md)。
- 各芯片最低 IDF 版本：UNVERIFIED，不写死。

## Contracts（设备契约）

1. **eFuse 一次性**：烧录/写保护/撤销不可逆；任何"烧"的动作前必须复述对象与后果并获确认。
2. **公钥摘要入 eFuse 后**：须写保护，但**不可读保护**（软件校验需读取摘要；误开读保护会导致无法启动，基线高置信）。
3. **私钥永不进设备**：签名发生在主机侧；设备只持有公钥摘要。
4. **FE 密钥不可读回**：密钥存 eFuse block1，烧录后写+读保护，软件不可读回。
5. 反幻觉红线：efuse block 编号、KEY_PURPOSE 取值等仅引用 [sb2-facts](references/sb2-facts.md) 中标注置信度的条目，其余不编造。

## Secure Boot v2 要点（基线高置信摘录）

- 签名方案：ESP32（rev 3.0+）与 ESP32-C3 官方页描述 **RSA-3072（RSA-PSS）**。
- 公钥 **SHA-256 摘要烧入 eFuse**（ESP32: BLK2；C3: BLOCK_KEY0-5 + KEY_PURPOSE=SECURE_BOOT_DIGESTX）。
- 摘要槽：ESP32 仅 1 个；C3 最多 3 个（`KEY_REVOKEX` 撤销，**不可逆**，支持保守/激进撤销策略）。
- 完整事实表与置信度标注 → [sb2-facts](references/sb2-facts.md)。

## Flash Encryption 要点（基线高置信摘录）

- AES-256（硬件引擎）；密钥存 eFuse block1，烧录后写+读保护、软件不可读回。
- **Development 模式：明文串口烧录 ≤ 3 次**（FLASH_CRYPT_CNT 计数）——开发期用第 3 次之前就该意识到节奏。
- **Release 模式：烧保护位后无法再明文烧录**，新镜像只能经 OTA——启用前确认 OTA 通道可用（→ `esp32-ota`）。

## 与 OTA 的关系

- 组合目标：**signed app + encrypted flash**——SB 防篡改/防换镜像，FE 防读flash 拿固件与密钥。
- FE Release 模式下 OTA 是唯一升级通道；OTA 镜像须为签名镜像，防回滚需求（secure_version 入 eFuse，仅可递增）在本技能评估、实现在 `esp32-ota`。
- 启用顺序：先 SB 后 FE（标注为官方推荐顺序；**具体步骤以官方 security 文档为准，引用前运行时核验**——本基线未逐条抓取顺序条目）。
- 升级链路安全（HTTPS 等）属 `esp32-ota` 职责，本技能不重复。

## Capability Boundaries + Hand-off

| User Intent | Skill |
|---|---|
| 签名密钥入 git/CI 明文 | **refusal**：拒绝并给治理方案（Workflow 第 4 步 + key-governance） |
| OTA 回滚开关/升级实现 | `esp32-ota` |
| 发布命名/校验和/制品门禁（密钥治理对接） | `fw-release-gate` |
| 真机验证安全启动行为 | `fw-hil-testing` |
| 启用后无法启动/崩溃 | `esp32-debug`（串口日志 + coredump） |
| 加密镜像异常的升级排障 | `esp32-ota` |

超界：TPM/可信执行类方案设计、云端 KMS 集成实现——仅指向官方文档，不展开。

## Workflow（量产前启用：先演练后烧录）

1. **定方案**：按芯片核对 SBv2 支持与算法（sb2-facts）；决定 SB only / SB + FE 组合；FE Release 前提 = OTA 通道就绪。
2. **开发阶段 rehearsal（必做）**：在**不烧生产 eFuse** 的前提下走通全流程——密钥生成、签名、开发模式 FE（≤3 次明文烧录纪律）、OTA 签名镜像升级、失败回滚；演练结论留档。
3. **密钥治理落位（烧录前门禁）**：按 [key-governance](references/key-governance.md) 完成——生成/离线保管/访问记录；**生产私钥从未进仓库与 CI 明文**；撤销预案（C3 槽位与 KEY_REVOKEX 不可逆）写清。
4. **生产烧录**：在产线按官方 security 文档流程烧录 eFuse（命令参数运行时核验）；先小批量试产验证开机、OTA、升级失败回滚，再放量。
5. **验收**：Validation Gates 全过；真机证据 → `fw-hil-testing`；制品与校验和门禁 → `fw-release-gate`。

## Validation Gates

1. 演练记录：签名流程、FE 开发模式烧录次数账本、OTA 签名镜像升级成功——全部有据可查。
2. 篡改实验（真机）：刷入被改动的镜像 → 设备拒绝启动（SB 生效证据）。
3. 读保护红线复核：公钥摘要 eFuse 只写保护、未读保护，设备可正常启动。
4. 小批量试产：≥3 台设备完成烧录 + OTA 升级 + 断电回滚，记录在案（无真机 = Pending HIL）。
5. 治理审计：确认生产私钥只存在于保管约定位置，git 历史/CI 日志无密钥（含历史提交）。

## Pitfalls

1. **不要**把 secure boot 私钥提交进 git 或放进 CI 明文变量——"方便 CI"不是理由；泄露后只能靠不可逆的槽位撤销止损。
2. **不要**跳过 rehearsal 直接对量产设备烧 eFuse——一次性烧错（错 block/误开读保护）无法撤销。
3. **不要**给公钥摘要开 eFuse 读保护——软件校验需要读它，读了会无法启动。
4. **不要**在没建好 OTA 通道前启用 FE Release 模式——之后新镜像只能 OTA 进去。
5. **不要**写 ED25519 相关方案归属——UNVERIFIED；算法问题只引用 sb2-facts 已标注条目。
6. **不要**把 FE 开发模式的"3 次明文烧录"当无限额度消耗在试错上——留最后次数给真正需要的验证。
7. **不要**假设所有芯片 SBv2 细节一致（槽数、block 布局不同）——按目标芯片查 sb2-facts。

## Official Sources

- [Secure Boot v2 (ESP32)](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/security/secure-boot-v2.html)
- [Secure Boot v2 (ESP32-C3)](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/security/secure-boot-v2.html)
- [Flash Encryption (ESP32)](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/security/flash-encryption.html)
- [ESP-IDF Security 总览](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/security/index.html)

## Privacy

签名密钥、efuse 配置、设备安全状态属最高敏感级：本 Skill 不采集、不存储、不外发任何密钥材料；示例一律占位符；用户贴出的密钥片段要提示立即轮换并按泄露流程处理（key-governance §5）。
