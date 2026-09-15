# GE · ESP32 MCU HIL 验收矩阵（fw-hil-testing 黄金示例）

**徽章**：`B0 Build Verification Only`（矩阵文档，需真机验证）

---

## 验收矩阵（10 项）

| # | 验收项 | 前置条件 | 操作 | 观察手段 | 预期 | 证据形式 | 徽章 |
|---|---|---|---|---|---|---|---|
| 1 | 上电启动 | 固件烧录完成 | 通电 | 串口 monitor | bootloader → app 启动日志 | 串口日志 | B2 |
| 2 | Hello World 输出 | esp32-idf hello_world | idf.py flash + monitor | 串口 | "Hello World!" 每 10s | 串口日志 | B2 |
| 3 | GPIO 控制 | LED 接线正确 | 调用 gpio_set_level | 万用表/LED | GPIO 高低电平切换 | 万用表读数 | B2 |
| 4 | Wi-Fi 连接 | 配网完成 | 设备启动 | 路由器 DHCP 列表 | 设备获取 IP | 截图 | B2 |
| 5 | OTA 成功 | 双分区已配置 | idf.py ota + 远程服务器 | 串口 | "OTA complete" + 新版本号 | 串口日志 | B2 |
| 6 | OTA 回滚 | Rollback 启用 | OTA 新版 → 不确认 valid → 重启 | 串口 | 自动回滚到旧版 | 串口日志 | B2 |
| 7 | 深睡唤醒 | esp_sleep_enable_timer_wakeup | 进入深睡 → 等待唤醒 | 串口 | 定时唤醒后正常启动 | 串口日志 | B2 |
| 8 | 看门狗恢复 | WDT 启用 | 任务阻塞超过 WDT 超时 | 串口 | 自动重启 + panic 日志 | 串口日志 | B2 |
| 9 | Secure Boot 签名验证 | eFuse 已烧签名公钥 | 烧录未签名固件 | 串口 | 启动失败（签名验证失败） | 串口日志 | B2 |
| 10 | 电流测量 | 万用表/功率计 | 设备各状态电流 | 功率计 | 深睡 < 运行 / µA 数值以实测为准 | 测量读数 | B2 |

## 说明

- µA 数值全部以实测为准（基线 UNVERIFIED），验收表不预设具体数字
- Secure Boot 测试为**破坏性操作**（eFuse 烧录不可逆），必须在 rehearsal 阶段用开发密钥验证
