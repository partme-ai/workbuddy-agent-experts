# GE · ota-rollback（esp32-ota 黄金示例）

**徽章**：`B0 Build Verification Only`

## 与 SKILL.md 映射

- §Core trap: `esp_ota_mark_app_valid_cancel_rollback()` 未调用 → 重启回滚 → `ge_ota_mark_valid()` 示例
- §Workflow: `esp_ota_begin` → `write` → `end` → `set_boot_partition` → `mark_valid` 顺序
- §Pitfalls: "Offset 禁止手填" → CSV 全部留空，由系统自动排布
- §Pitfalls: "分区偏移不编造" → ge-ota-minimal.csv

## 验证

```bash
head -1 ge-ota-minimal.csv | grep -q "^# Name" && echo "CSV header OK"
grep -c "esp_ota_mark_app_valid_cancel_rollback" ge-ota-rollback.c
```
