# GE · procd-service（openwrt-procd-init 黄金示例）

**徽章**：`S1 Executable Evidence`（脚本语法正确，可在 OpenWrt 上运行；非完整构建）

## 被测物

| 文件 | 模式 | 关键验证点 |
|---|---|---|
| `ge-example-procd.sh` | USE_PROCD=1 | command 数组（每参一元素）、respawn(3600/5/5)、env/file/limits/stdout-stderr、service_triggers + PROCD_RELOAD_DELAY |
| `ge-example-legacy.sh` | legacy | service_start/stop、PID 文件、logger |

## 与 SKILL.md 的映射

| SKILL.md 章节 | 对应示例 |
|---|---|
| §Workflow 1: procd 服务骨架 | `ge-example-procd.sh` |
| §Pitfalls: "不要写 start() 改写 start_service()" | `ge-example-legacy.sh`（legacy 模式下才用 start/stop） |
| §Pitfalls: "command 数组每参一元素" | `ge-example-procd.sh` L15（`"$SERVICE_BIN" --config ...` 两参数分开） |
| §References: procd-instance.md | respawn/env/file/limits 参数表在 `ge-example-procd.sh` 中逐行注释 |

## 验证

```bash
sh -n ge-example-procd.sh && echo "procd syntax OK"
sh -n ge-example-legacy.sh && echo "legacy syntax OK"
head -1 ge-example-procd.sh | grep -q 'rc.common' && echo "shebang OK"
```

## 踩坑备忘

1. `procd_set_param command` 的参数是**独立函数实参**，不能拼成一个带空格的字符串。
2. `respawn` 三参数含义：`(窗口秒数, 超时秒数, 最大重试次数)`——默认 `(3600, 5, 5)` 即 1 小时内最多重启 5 次。
3. legacy 模式的 `start()` 会被 rc.common 覆盖——脚本声明了 `USE_PROCD=1` 后系统自动走 `start_service()`，`start()` 不会被调用。
