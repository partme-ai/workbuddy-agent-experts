# GE · deep-sleep（esp32-lowpower 黄金示例）

**徽章**：`B0 Build Verification Only`

## 与 SKILL.md 映射

- §Pitfalls: "µA 数值 UNVERIFIED 禁止写入" → 注释标注"以功率计实测为准"
- §Workflow: timer wakeup → `esp_sleep_enable_timer_wakeup()` + `esp_deep_sleep_start()`
- §Pitfalls: "唤醒源因芯片而异" → EXT0 GPIO 注释标注 datasheet 核验
- §References: wakeup-sources.md → 6 类唤醒源
- §References: sleep-modes.md → deep/light sleep 区分

## 验证

```bash
idf.py set-target esp32c3 && idf.py build  # 编译通过即 B0
```
