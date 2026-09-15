# GE · release-check（fw-release-gate 黄金示例）

**徽章**：`S1 Executable Evidence`（脚本可在 macOS/Linux 上运行）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-release-check.sh` | 5 项检查（产物存在/校验和/命名规范/外链扫描/密钥泄露），pass/fail 计数，全绿 exit 0 |

## 与 SKILL.md 映射

- §Workflow: "发布前检查单" → 5 项逐一对应
- §Pitfalls: "密钥不进产物" → L48-50 密钥泄露扫描
- §References: naming-and-versioning.md → `openwrt_tinynas-*` 五段式前缀
- §References: release-checklist.md → 检查单完整性

## 验证

```bash
bash -n ge-release-check.sh && echo "syntax OK"
chmod +x ge-release-check.sh
# 模拟测试：无参数应提示 usage
./ge-release-check.sh 2>&1 | grep -q "usage" && echo "usage guard OK"
```
