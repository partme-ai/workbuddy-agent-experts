# 总线速查（bus-quickref）

read-when：写 I2C/SPI/UART 驱动代码前，确认接口方向与配置要点。
基线：ESP-IDF v6.1，走读 2026-09-02。**只有标"已核验"的头文件名可直接引用；其余标"运行时核验"。**

## 驱动接口方向（v6.x）

| 总线 | 状态 | 头文件 |
|---|---|---|
| I2C master | 新式组件化驱动（`esp_driver_i2c` 组件；CMakeLists `REQUIRES esp_driver_i2c`）——2026-09-02 官方 stable 文档**已核验** | `driver/i2c_master.h`（slave：`driver/i2c_slave.h`） |
| I2C legacy | 新式页已不收录；**旧工程迁移时**按 Migration Guides 核验处置 | — |
| SPI / UART | 新式驱动方向（组件化），**头文件名未抓取 → 运行时核验**：查本机 IDF `components/` 或官方 API 参考 | — |
| ADC / I2S / Timer | legacy 已在 **v6.0 移除**（基线高置信），必须用新接口 | 见 adc-caveats 与官方迁移指南 |

核验命令（本机 IDF 源码树）：

```bash
find "$IDF_PATH/components" -maxdepth 3 -path "*include/driver/*" -name "*i2c*"
find "$IDF_PATH/components" -maxdepth 3 -path "*include/driver/*" -name "*spi*"
find "$IDF_PATH/components" -maxdepth 3 -path "*include/driver/*" -name "*uart*"
```

## I2C 速查

- 配置要点：主频从器件手册上限取保守值（常见 100k/400k 档，具体以器件为准）；7 位地址与 8 位写法不要混用。
- 上拉：I2C 开漏总线，按总线电容与速率核算上拉阻值；芯片内部上拉偏弱，外置上拉更可靠（电气结论以实测为准）。
- 排障：无 ACK → 查地址写法/速率/上拉/共地；有逻辑分析仪直接看波形（→ fw-hil-testing）。

## SPI 速查

- 四要素核对：CPOL/CPHA（mode 0–3）、片选极性与时序、字节序、时钟速率。
- 排障顺序：mode 不对是最常见根因；速率先降档验证再提回。

## UART 速查

- 三要素一致：波特率、数据位/校验/停止位；TTL 电平匹配（3.3V），别接 RS232 电平。
- 调试 console 与业务 UART 分开规划；烧写/monitor 走的串口别被业务占用。

## 通用纪律

1. 头文件不确定 → 本机源码树 find + 官方 API 参考，**不背记忆**。
2. 引脚/复用/上拉 → 芯片 datasheet + 板原理图（SKILL.md 硬件契约）。
3. ISR 与总线驱动的并发 → 移交 `esp32-freertos`。
4. 每次只改一个总线参数，改完实测；无硬件证据标注 `Build Verification Only`。
