# v5 → v6 迁移清单（v5-to-v6-migration）

read-when：v5 工程在 v6.x 下编译报错，或评估升级。
基线：ESP-IDF v6.1，走读 2026-09-02。本文件只写基线抓到的破坏性变更；清单之外的不猜。

## 版本背景（引用必带日期）

- 截至 2026-09-02：最新 stable **v6.1**（2026-08-27 发布，官方描述为 "minor update for ESP-IDF v6.0"）；v6.0 线 **v6.0.2**（2026-06-29）；最新 v5.x 维护版 **v5.5.5**（2026-07-17）。
- 官方不用 "LTS"，采用 30 个月支持期（12 个月 Service + 18 个月 Maintenance）。
- 受支持版本清单（v6.1/v6.0.2/v5.5.5/v5.4.4/v5.3.5/v5.2.7）来自搜索转述，**中置信**，引用前用官方 versions 页核验。

## 破坏性变更（基线高置信）

1. **v6.0 移除大量旧版（legacy）驱动**——基线明确点名 ADC、I2S、Timer 等。
   - 症状：升级后头文件找不到 / 符号未定义，报错指向 `driver/adc*`、`driver/i2s*`、`driver/timer*` 一类旧头。
   - 处理：改用对应新式驱动接口；**准确的新头文件名以本机 IDF 源码树（components/ 目录）或官方 API 参考为准**（运行时核验），不要背清单。
2. **v6.1 将 esp-mqtt 移入组件管理器**——不再内置，需在 `idf_component.yml` 声明 `espressif/mqtt` 依赖（`idf.py add-dependency espressif/mqtt`）。
   - 症状：v5 工程直接 build 时 mqtt 头文件/组件缺失。

## 迁移流程（确定性步骤）

```bash
idf.py --version                 # 1. 确认本机大版本
idf.py build 2>&1 | tee v6-build.log   # 2. 存全量报错
# 3. 按 log 逐类归因：legacy 驱动 / esp-mqtt / 其他
# 4. 逐类修复：换新式接口；mqtt 加组件依赖
idf.py build                     # 5. 每修一类重验一次
```

- 每类错误单独提交，出问题可回退。
- 示例代码优先参考**当前 IDF 版本的官方 examples/**，而不是网上 v5 时代的博客代码。

## UNVERIFIED 项（保留标注，禁止写死）

以下内容基线未抓到，**不得在答案中断言**，只给核验方法：

| UNVERIFIED 项 | 核验方法 |
|---|---|
| 被 v6.0 移除驱动的完整清单与新头文件名 | 官方 Migration Guides（docs.espressif.com → Migration Guide）+ 本机 components/ 目录实查 |
| 各芯片最低支持 IDF 版本 | 官方 stable 文档按 target 切换 + release notes，见 esp32-variants 技能 |
| ED25519 Secure Boot 方案归属 | 官方 secure-boot-v2 页按芯片核对 |
| ESP32-C5 / ESP32-S31 的能力细节 | 官方选型页与 release notes |

## Pitfalls

1. **不要**为"快速修好"把 IDF 降回 v5 了事——先确认项目锁定版本与依赖（dependencies.lock）是否允许。
2. **不要**混用 v5 的例程代码与 v6 的新式驱动——同一外设两套 API 并存时编译可能过、运行语义不同。
3. **不要**凭记忆回答"哪个版本移除了哪个 API"——以本机构建报错与官方迁移指南为准。
