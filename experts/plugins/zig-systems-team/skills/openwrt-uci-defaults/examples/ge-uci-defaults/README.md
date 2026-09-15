# GE · uci-defaults（openwrt-uci-defaults 黄金示例）

**徽章**：`S1 Executable Evidence`（脚本可在 OpenWrt 上运行验证）

## 被测物

| 文件 | 验证点 |
|---|---|
| `ge-uci-defaults-boot.sh` | 幂等（`[ -f ... ] && exit 0`）、`uci -q get ... >/dev/null \|\| set` 补缺、`exit 0` 结尾 |
| `ge-uci-config-sample` | UCI 格式、SMB2/3 + NetBIOS、`name_resolve_order bcast host` |

## 与 SKILL.md 映射

- §Workflow: "先查再设，不覆盖已有值" → `uci -q get ... >/dev/null || uci set ...`
- §Pitfalls: "uci-defaults 必须 exit 0" → L15 `exit 0`
- §Pitfalls: "不要在 uci-defaults 里 curl 外网" → 全部本地配置，无网络依赖
- §Pitfalls: "时区配置" → `timezone='CST-8'` / `zonename='Asia/Shanghai'`

## 验证

```bash
sh -n ge-uci-defaults-boot.sh && echo "syntax OK"
tail -1 ge-uci-defaults-boot.sh | grep -q '^exit 0$' && echo "exit 0 OK"
```
