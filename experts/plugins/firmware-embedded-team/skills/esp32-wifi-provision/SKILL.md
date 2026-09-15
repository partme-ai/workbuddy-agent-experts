---
name: esp32-wifi-provision
license: Apache-2.0
description: Choose and implement ESP32 Wi-Fi provisioning with ESP-IDF — method selection across the four official approaches (Unified Provisioning over SoftAP/BLE transports with Security 0/1/2, legacy SmartConfig, Wi-Fi Easy Connect/DPP, raw protocomm), the provisioning state machine (未配网 → 配网中 → 已配网 → 凭据失效重配), NVS-backed credential persistence, and production security red lines (不把 SSID/密码写死固件、Production 禁 Security 0). Use when the user says 配网/联网配置/烧 Wi-Fi 凭据, asks SmartConfig 还是 BLE 配网 / Unified Provisioning 怎么接, integrates the network_provisioning component, or reports 配网失败/连不上路由器/重配网. Do NOT use for firmware update delivery (route esp32-ota), chip selection when the target lacks Wi-Fi/BLE (route esp32-variants), or Thread/Zigbee connectivity.
---

# ESP32 Wi-Fi Provisioning（配网）

配网是把 Wi-Fi 凭据安全地送进设备的过程。本 Skill 先做方式选型，再给出状态机与安全红线；**不凭记忆编造传输层细节**——凡基线未抓取的参数标注"运行时核验"。

## Determine Task Type

1. **产品量产选型**：还没有定配网方式，要从四种官方方式里选 → 先读选型表 + [provisioning-comparison](references/provisioning-comparison.md)。
2. **已定方式要实现**：如"Unified Provisioning + BLE + Security 2"→ Workflow 第 3 步起，安全方案细节读 [security-scheme](references/security-scheme.md)。
3. **配网排障**：配得上但连不上、重配网不生效、Security 握手失败 → Workflow 第 5 步 + Pitfalls。
4. **凭据生命周期**：改密码/换路由器后的重配策略 → 状态机"凭据失效"分支。

## Prerequisites / Preflight

先运行时核验，缺一项就问，不要猜：

```bash
idf.py --version          # 确认 IDF 版本（基线见 Offline Baseline）
idf.py list-targets 2>/dev/null | head -5 || echo "IDF not in PATH"
```

1. **目标芯片**：有没有 Wi-Fi？有没有蓝牙？（红线见 Contracts——H2/P4 无 Wi-Fi 射频，S2 无蓝牙）
2. **配套手机 App**：能否要求用户装 ESP BLE Provisioning / ESP SoftAP Provisioning 官方 App？
3. **RAM 预算**：BLE 传输约需 110KB RAM（基线高置信）——小内存方案先确认。
4. **组件现状**：项目里用的是现行组件 `network_provisioning` 还是旧组件 `wifi_provisioning`（见 references/comparison 的迁移段）。

## Offline Baseline

- ESP-IDF 基线 = **v6.1**（最新 stable，截至走读 **2026-09-02**，不自动更新）；配网四种方式、Security 0/1/2、SoftAP/BLE 传输引自基线 §7（抓取官方 provisioning 文档，置信度高）。
- **NVS 持久化凭据：基线标注"运行时核验"**——官方抓取页未直接确认，本 Skill 沿用该标注，实现后必须在真机验证重启后凭据仍在（Validation Gate 3）。
- 版本之后的行为变化以官方 provisioning 文档为准，不凭记忆断言。

## Contracts（设备契约）

- **芯片无线能力红线（高频错误点，基线高置信）**：ESP32-H2 **无 Wi-Fi**；ESP32-P4 **无片上射频**（需 ESP-Hosted 等伴生方案）；ESP32-S2 **无蓝牙**（不能选 BLE 传输）。选型前先核对，对不上就停下来。
- **不硬编码凭据**：SSID/密码不得写死在固件源码或 sdkconfig 默认值里随镜像分发（见安全红线）。
- 配网会写入 NVS/Flash：批量操作或回收设备时注意凭据残留，不做"默默清空用户数据"的动作，执行前告知。
- 具体手机端 App 版本、组件 registry 上的准确包名与版本号：以运行时 `idf.py add-dependency` 查询结果为准。

## 四种官方方式选型（基线 §7，高置信）

| 方式 | 机制 | 传输 | 适用 | 备注 |
|---|---|---|---|---|
| **Unified Provisioning（推荐）** | 基于 protocomm 的统一配网协议 | SoftAP(+HTTP) 或 BLE(GATT) | 绝大多数量产产品 | Security 0/1/2 可选（默认选 2）；有官方 iOS/Android App |
| SmartConfig |legacy，UDP 广播类机制 | 空口广播 | 仅存量兼容 | 可靠性弱、依赖网络环境，新产品不建议；细节以官方文档为准 |
| Wi-Fi Easy Connect (DPP) | Wi-Fi 联盟 Easy Connect | 扫码/频道引入 | 强互操作诉求 | 基线仅确认"存在"，参数细节运行时核验 |
| protocomm 直用 | 底层传输+安全方案底座 | 自定义 | 有自定义 App/协议团队 | Unified Provisioning 的下层；直接用时自行承担协议设计 |

选型判据明细（RAM、App 门槛、迁移旧组件、异常重试设计）读 [provisioning-comparison](references/provisioning-comparison.md)。

## 配网状态机

```text
未配网(UNPROVISIONED)
    -> 收到配网请求 -> 配网中(PROVISIONING)   [指示灯/提示用户]
    -> 凭据下发 + 尝试连接
    ├── 连上并确认在线 -> 已配网(PROVISIONED)
    └── 连接失败(密码错/信号弱) -> 停留并回报错误 -> 回到 配网中 或 未配网
已配网
    └── 凭据失效(改密/路由器更换/认证超时) -> 凭据失效重配(RE-PROVISION)
        -> 重新进入 配网中（旧凭据失效处理策略见 references/comparison §4）
```

每台设备必须持久化"是否已配网"这一状态；重启后据此决定直接连 Wi-Fi 还是进配网模式。

## Capability Boundaries + Hand-off

| User Intent | Skill |
|---|---|
| 配网完成后做固件升级通道 | `esp32-ota` |
| 芯片没有 Wi-Fi/蓝牙或选型纠结 | `esp32-variants` |
| 配网服务占用任务/队列设计 | `esp32-freertos` |
| 低功耗下配网窗口（深睡唤醒再配） | `esp32-lowpower` |
| 工程骨架/分区表/烧写 | `esp32-idf` |
| 真机验收配网全流程 | `fw-hil-testing` |

超界：BLE/SoftAP 之外的自定义传输协议设计、手机 App 开发本身——本 Skill 只给协议选型与设备侧，App 侧仅指向官方 App。

## Workflow

1. **核验环境**：Preflight 命令 + 芯片无线能力核对（Contracts 红线）。
2. **选型**：按选型表定"传输 + 安全方案"；量产默认 **Unified Provisioning + Security 2**，传输按 App/RAM 预算选 BLE 或 SoftAP。
3. **接入组件**：`idf.py add-dependency <network_provisioning 组件名=版本>`（准确命名空间与版本以 registry 运行时查询为准，写入 `idf_component.yml`）；旧组件 `wifi_provisioning` 项目按 references/comparison §5 评估迁移。
4. **实现状态机**：持久化配网状态；配网中提供用户可感知指示；失败必须回报具体错误（错误码透传到 App），不静默重试。
5. **真机验证**：过 Validation Gates 1–4；NVS 持久化项按基线标注执行"运行时核验"。
6. **量产前**：安全方案复核实 [security-scheme](references/security-scheme.md) 红线；全流程真机验收 → `fw-hil-testing`。

## Validation Gates

1. 正常路径：官方 App 走完配网，设备连上目标路由器并拿到在线确认（如 MQTT/HTTP 心跳）。
2. 异常路径：故意输错密码 → 设备回报错误而非"假装成功"；超时有上限。
3. **持久化验证（运行时核验项）**：断电重启后设备自动重连，无需再次配网——此项基线未直接确认，必须在目标真机实测通过后才可声称支持。
4. 安全验证：Production 构建确认未编译进 Security 0；抓包/日志确认凭据不以明文出现在串口日志。
5. 无真机时：所有结论标 `Build Verification Only`，不得声称"配网已验证"。

## Pitfalls

1. **不要**把 SSID/密码写死进固件（源码、`Kconfig` 默认值、测试固件都算）——量产镜像带凭据等于把用户网络卖掉。
2. **不要**在 Production 环境用 Security 0（无加密）——配网信道上凭据可被直接截获。
3. **不要**给 S2 选 BLE 传输、给 H2/P4 排 Wi-Fi 配网任务——先核对芯片无线能力（Contracts）。
4. **不要**假设"写入 NVS 一定成功持久化"——这是基线标注的运行时核验项，真机重启验证前不得承诺。
5. **不要**给新产品选 SmartConfig 并承诺可靠性——它是存量兼容选项。
6. **不要**吞掉配网失败错误码——用户和 App 都需要知道是密码错还是超时。

## Official Sources

- [ESP-IDF Wi-Fi Provisioning 索引（四种方式）](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/provisioning/index.html)
- [Unified Provisioning 文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/provisioning/provisioning.html)
- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/)
- [Espressif 组件注册表（network_provisioning）](https://components.espressif.com)

## Privacy

本 Skill 处理的 SSID/密码是用户网络凭据：不采集、不存储、不外发；示例与日志一律使用占位符（如 `SSID_PLACEHOLDER`），并要求使用者不要把真实凭据贴进 issue、日志或代码仓库。
