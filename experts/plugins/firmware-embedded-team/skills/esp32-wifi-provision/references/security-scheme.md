# Security Scheme：Security 0 / 1 / 2 与安全红线

来源：ESP-IDF 基线 §7（官方 Unified Provisioning 文档，走读 2026-09-02，置信度高）。不自动更新。

## 1. 三档安全方案

| 方案 | 机制 | 保护什么 | 何时可用 |
|---|---|---|---|
| Security 0 | 无加密 | 什么都不保护 | **仅开发/实验**；Production 禁用（红线） |
| Security 1 | Curve25519 密钥协商 + AES-256-CTR 会话加密；可选 Proof of Possession (PoP) | 凭据在配网信道上加密 | 兼容存量实现时可用 |
| Security 2 | SRP6a 认证 + AES-256-GCM 会话加密 | 凭据加密 + 对端认证（防中间人/仿冒配网端） | **推荐默认** |

## 2. 选型规则

1. 新产品一律 Security 2，除非有已确认的存量兼容约束。
2. 用 Security 1 时必须设置 PoP（口令防仿冒）；PoP 本身是共享秘密，按凭据同等对待（不进日志、不进仓库）。
3. Security 0 只允许出现在：开发板 + 开发 Wi-Fi + 非发布固件的实验里；任何"量产/出厂"构建出现 Security 0 即验收失败。

## 3. 红线（违反即拒答/打回）

1. **不把 SSID/密码写死固件**：源码、`Kconfig` 默认值、`sdkconfig.defaults`、单元测试 fixture 一律不允许出现真实凭据。
2. **Production 禁 Security 0**：发布构建的安全方案在 Validation Gate 复核，不是"以后再改"。
3. **凭据不落日志**：串口日志、coredump、上传的诊断包里出现明文凭据 = 事故；日志打印凭据前先脱敏。
4. **PoP/口令按凭据管理**：与 SSID/密码同级别，不进仓库、不进 CI 明文（治理细则对接 `fw-release-gate` 的发布门禁模式）。

## 4. 验证方法（每档都要跑）

1. Security 2 配网成功 + 错误口令被拒（SRP6a 认证失败路径）。
2. 配网过程串口日志抽查：无明文 SSID/密码/PoP。
3. Security 1/0 存量路径如保留：在发布检查单里单列并说明理由与范围。
4. 无真机时标注 `Build Verification Only`；真机全流程 → `fw-hil-testing`。

## 5. 反幻觉边界

- 各方案的报文格式、握手步数、密钥派生细节超出基线抓取范围：回答"以官方 provisioning 文档为准（运行时核验）"，不凭记忆展开。
- Security 方案与芯片无关（是协议层选择），但**传输层与芯片相关**（S2 无蓝牙）——别把两层混为一谈。
