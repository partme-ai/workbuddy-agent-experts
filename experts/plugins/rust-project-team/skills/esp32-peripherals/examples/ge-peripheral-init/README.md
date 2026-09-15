# GE · peripheral-init（esp32-peripherals 黄金示例）

**徽章**：`B0 Build Verification Only`（代码片段，需 IDF 环境编译验证）

## 与 SKILL.md 映射

- §Pitfalls: "禁止编造 Strapping 引脚值" → 引脚号均标"以板实测为准"
- §Workflow 1: "核验后的引脚号必须显式写入驱动初始化配置" → `BLINK_GPIO` / `UART_TX_PIN` 显式定义
- §Hand-off: "IDF 版本升级/v5→v6 迁移 → esp32-idf" → v6 新驱动头文件方向注释
- §References: bus-quickref.md → UART 波特率/数据位/停止位

## 验证

```bash
idf.py set-target esp32c3 && idf.py build  # 编译通过即 B0
```
