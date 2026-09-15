# GE · storage-mount（openwrt-storage-mount 黄金示例）

**徽章**：`B0 Build Verification Only`（配置文件，需 OpenWrt 环境验证）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-hotplug-disk-monitor` | 序号 50（>10）、`[ "$ACTION" = "add" ]` 守卫、只判断不挂载、`logger` 记录 |
| `ge-fstab-config` | UCI fstab 格式、`auto_mount` 开启、ext4 rw |

## 与 SKILL.md 映射

- §Pitfalls: "不自写挂载 hotplug 与 10-mount 竞争" → 序号 50，只做补充动作
- §Pitfalls: "附加脚本用 >10 序号" → 文件名 `ge-hotplug-disk-monitor`（50-前缀）
- §Workflow: "fstab 由首启 uci-defaults 自动生成" → `ge-fstab-config` 作为手动补充
- §References: fstab-uci.md → mount 配置块格式

## 验证

```bash
sh -n ge-hotplug-disk-monitor && echo "syntax OK"
```
