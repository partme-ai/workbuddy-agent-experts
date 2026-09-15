# GE · coredump-parse（esp32-debug 黄金示例）

**徽章**：`S1 Executable Evidence`（脚本可运行，IDF 未安装时 SKIPPED）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-coredump-parse.sh` | IDF 检测、输入文件检查、`idf.py coredump-info` 封装、未安装时 SKIPPED |

## 与 SKILL.md 映射

- §Workflow: "coredump 提取 → 符号化调试" → `idf.py coredump-info -c -e`
- §Pitfalls: "SWD 不支持（ESP32 原生）" → 只用 JTAG/OpenOCD
- §Pitfalls: "缓解类观察项仅作假设交付" → crash-triage checklist 第 5 项
- §References: crash-triage.md → panic/WD/brownout 分类

## 验证

```bash
bash -n ge-coredump-parse.sh && echo "syntax OK"
chmod +x ge-coredump-parse.sh
./ge-coredump-parse.sh 2>&1 | head -1  # 无参数应报 usage
```
