---
name: fw-release-gate
license: Apache-2.0
description: Operate the firmware release gate — naming and versioning with SemVer plus channel/watermark fields (five-segment image-name pattern 提炼自 TinyNAS 实践 openwrt_<brand>-<tier>-<device>_v<SemVer>-<channel>_<date>.img.gz), artifact integrity (mandatory sha256 sidecar re-verified at the gate, SOURCE_DATE_EPOCH reproducible-build declaration, LICENSE/GPL compliance for OpenWrt GPLv2 and bundled AGPL components), signing and key governance (asymmetric pattern 固件只嵌公钥/私钥仅签名机/渠道子密钥分发, with the symmetric short-code boundary stated as risk), and a scriptable pre-release checklist (artifacts+checksums, name lint, zero external links, secret scan, rollback plan, HIL badge requirement, release notes with known issues). Use when the user asks 镜像发布前检查什么 / 固件怎么命名 / 版本号怎么定 / 校验和 / 渠道固件 / 发布流程, proposes 把签名私钥放进 CI 环境变量 (refuse with a governance plan), or asks 多渠道能否共用一把签名密钥. HIL evidence gaps route back to fw-hil-testing; ESP32 secure-boot/eFuse mechanics route to esp32-secureboot.
---

# 固件发布门禁（fw-release-gate）

发布门禁 = **可脚本化的事实检查**，不是"感觉可以了"。产物、命名、校验和、许可证、密钥、回滚预案、HIL 徽章——逐项过，任一失败即不发布。门禁没拦住坏产物的门禁等于没有。

## Determine Task Type

1. **发布前门禁（主路径）**：镜像要发渠道/用户 → Workflow A（检查单逐项过）。
2. **命名与版本决策**：怎么命名、版本号怎么加、渠道字段怎么打 → Workflow B + [naming-and-versioning](references/naming-and-versioning.md)。
3. **签名与密钥治理**：用什么方案签、密钥放哪、多渠道怎么分 → Workflow C + 本页"签名与密钥治理"。
4. **完整性/复现性排障**：sha256 对不上、两次构建不一致 → Workflow D。

## Prerequisites / Preflight

```bash
# 产物与校验和工具就位（占位路径按项目替换）
ls -l bin/targets/*/ 2>/dev/null || ls -l out/ 2>/dev/null || echo "no artifact dir found"
command -v sha256sum || command -v shasum || echo "no sha256 tool"
```

1. 产物目录、目标渠道、目标设备清单在手；
2. 该版本的 HIL 徽章记录在手——没有 → 路由 `fw-hil-testing`，本门禁不放行"稳定版"；
3. 签名方案的密钥归属已明确；没明确 → 先过下面"签名与密钥治理"，再谈发布。

## Offline Baseline

- 走读日期 **2026-09-02**，不自动更新。
- OpenWrt 基线 **25.12.5**；五段式命名模式提炼自 TinyNAS 闭环实践（其规格基线 2026-08-31）。
- OpenWrt 侧可复现构建机制（`SOURCE_DATE_EPOCH`）细节在 `openwrt-image-build` 的 reproducible-build reference；本 Skill 只消费其结论（固定 epoch 重构建、哈希应一致、漂移排查顺序）。

## Contracts（发布物契约）

1. **sha256 必附**：每个发布物必须有成对 `.sha256`（内容 = `<hash>  <filename>`），且门禁**重算**通过——"构建时算过"不算数。
2. **可复现构建声明**：发布记录写明 `SOURCE_DATE_EPOCH` 取值与来源；无法复现时如实标注，禁止声称 deterministic。
3. **LICENSE/GPL 合规**：分发二进制必须满足所含组件的许可证义务——OpenWrt 本体 GPLv2（附源码获取途径与构建脚本）；随包 AGPL/MIT/Apache 组件逐一对清单。模式提醒：网络服务型 AGPL 组件（Alist 类）的义务形态与 GPLv2 不同，单列一行检查。发布说明附许可证清单。
4. **HIL 徽章前置**：进渠道并宣称"可用/稳定"的版本，徽章必须 ≥ `HIL Verified`（语义 → `fw-hil-testing`）；`Build Verification Only` / `Boot Verified (QEMU)` 只能进内部/测试渠道并显式标注。
5. 反幻觉红线：版本号、日期、渠道字段必须来自构建记录（epoch/CI 输出），禁止手填"大概日期"。

## 签名与密钥治理（模式）

**商业授权与完整性优先非对称签名**，三条治理不变式：

1. **固件/设备只嵌公钥（或公钥摘要）**——验签能力公开无妨；
2. **私钥只存在于构建/签名机**（离线机或受控签名服务），永不进 git、CI 明文变量、日志、聊天记录；
3. **渠道子密钥分发**：根密钥只签发渠道子密钥/子产物，某渠道泄露只作废该渠道子钥，不动根。

**对称短激活码的适用边界**（一句话模式）：对称方案 = 固件必须内含铸码/校钥能力，提取固件即等于拿到铸码能力；非对称方案 = 提取固件只有验签公钥，**不可铸码**。因此对称短码仅适用于低价值、可接受克隆风险的场景；商业授权一律优先非对称。ESP32 侧 eFuse / Secure Boot v2 / Flash 加密机制 → `esp32-secureboot`（其 key-governance 与本节同一套治理原则）。

## 命名与版本策略（五段式模板）

模式引用（提炼自 TinyNAS 实践）——**五段式镜像名**，文件名即元数据：

```text
openwrt_<brand>-<tier>-<device>_v<SemVer>-<channel>_<date>.img.gz
```

- **SemVer**：MAJOR = 破坏兼容（分区布局/配置不迁移/不可降级）；MINOR = 新增功能；PATCH = 修复；
- **channel**：stable / beta / dev 进文件名，杜绝"同名不同质"；
- **date**：构建日期，取自构建记录（SOURCE_DATE_EPOCH / CI 输出），不是手填；
- 命名 lint 判则、裁剪规则与反例 → [naming-and-versioning](references/naming-and-versioning.md)。

## Capability Boundaries + Hand-off

| User Intent | Skill |
|---|---|
| HIL 证据不足 / 徽章不达标 | `fw-hil-testing`（本门禁的徽章前置） |
| 两次构建不一致 / 复现性机制 | `openwrt-image-build`（SOURCE_DATE_EPOCH 机制侧） |
| ESP32 安全启动 / eFuse / 加密 | `esp32-secureboot`（机制层） |
| OTA 升级包投放机制 | `esp32-ota`（升级产物校验回本 Skill） |
| 任务分型入口 | `fw-core` |
| CI/CD 平台本身搭建 | 超界：给通用建议，不替代本门禁清单 |

## Workflow A — 发布前检查单（主路径）

按 [release-checklist](references/release-checklist.md) 的脚本骨架逐项执行（风格对标生产门禁脚本：pass/fail 计数、全绿退出 0）：

1. 产物存在 + `.sha256` 成对且门禁重算一致；
2. 命名 lint：五段式各段合法，且文件名中的 device/version/channel/date 与构建记录一致；
3. 零外链扫描：随包前端/资源无公网 CDN 外链；
4. 密钥扫描：产物树与覆盖层无私钥/盐值/凭据（有意入库的测试密钥须显式豁免并公开标注）；
5. 回滚预案存在：上一个可用版本镜像 + 降级步骤成文；
6. HIL 徽章达标：发布说明载明徽章级别，渠道版 ≥ `HIL Verified`；
7. 发布说明：版本要点 + **已知问题**（没有也要写"已知问题：无"）；
8. LICENSE 清单附带。

任一项失败 → 修复后**重跑全单**（不是只补失败项）。

## Workflow B — 命名与版本决策

1. 按变更性质定 MAJOR/MINOR/PATCH（判则 → naming-and-versioning §2）；
2. 定渠道标签；确认渠道/版本/日期同步写入镜像内水印字段（值来自构建记录）；
3. 跑命名 lint（reference §4）；改名/改版后重跑发布检查单。

## Workflow C — 签名方案决策

1. 判定场景：固件完整性/防篡改 → 非对称签名；商业授权/激活 → 非对称许可证（设备只持公钥）；
2. 密钥落位：按"三条不变式"落位后再开工——有人提议把私钥放进 CI → refusal（见 Pitfalls 1）；
3. 多渠道：根钥 + 渠道子钥；子钥作废流程成文后才放行；
4. 有人提议对称短码 → 按"适用边界"评估，接受则留下书面风险声明，商业授权场景不接受。

## Workflow D — 完整性/复现性排障

1. sha256 不匹配：先排除传输截断（重下载、比大小），再排除"同名不同构建"（命名 lint 第 2 项）；
2. 两次构建不一致：固定 `SOURCE_DATE_EPOCH` 重构建两次比对哈希；仍不一致按"环境差异 → 覆盖层时间戳/随机 ID → ipk 仓库漂移"排查（机制细节 → `openwrt-image-build`）；
3. 结论写入发布记录——无法复现就如实标注，不改口"应该一样"。

## Validation Gates

- 检查单脚本全绿（退出 0），输出留档随发布归档；
- 抽查一条渠道链路：从下载点到设备，校验和 + 签名验证全程通过；
- 负向验证：故意破坏一项（改名/篡改镜像一个字节/删 .sha256），门禁必须拦截。

## Pitfalls

1. **不要**把签名私钥放进 CI 环境变量/仓库——明文变量会进日志、被子进程继承、落进镜像层；"仓库是私有的"不改变泄露面。正确姿势：构建与签名分离，CI 只留公钥摘要做验证性检查。
2. **不要**多渠道共用一把无派生关系的密钥——单点泄露全线沦陷且无法只作废一个渠道；用根钥 + 渠道子钥。
3. **不要**发布没有 `.sha256` 的产物，也不要只信"构建时算过"——门禁重算。
4. **不要**让文件名里的版本/渠道/日期与构建记录不一致——命名即元数据，错名比缺名更危险。
5. **不要**在 HIL 徽章不达标时对渠道放行"稳定版"——B0/B1 只能进内部/测试渠道并显式标注。
6. **不要**漏掉许可证义务——GPL/AGPL 组件的分发义务不因"只是刷固件"而消失。
7. **不要**在发布说明里隐去已知问题——已知问题不上报，售后代价更大。
8. **不要**用对称短码做商业授权——提取固件即可铸码；要用，先书面确认可接受克隆风险。

## Official Sources

- [Semantic Versioning](https://semver.org/)
- [SOURCE_DATE_EPOCH spec](https://reproducible-builds.org/docs/source-date-epoch/)
- [OpenWrt Image Builder](https://openwrt.org/docs/guide-developer/imagebuilder)
- [GNU GPLv2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
- [GNU AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html)
- [ESP-IDF Secure Boot v2](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/security/secure-boot-v2.html)
- [ESP-IDF Flash Encryption](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/security/flash-encryption.html)

## Privacy

门禁脚本只做本地检查，不上传产物与校验和；密钥材料不进日志与报告；密钥/凭据扫描命中时只报文件路径，不打印内容；发布说明中的渠道与设备信息按用户数据对待，外发前脱敏。
