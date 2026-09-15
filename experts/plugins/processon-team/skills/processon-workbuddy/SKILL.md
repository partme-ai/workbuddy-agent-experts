---
name: processon-workbuddy
description: ProcessOn invocation spec for WorkBuddy - MCP access (the http endpoint already configured in mcp.json, or the vendored stdio proxy as fallback), the diagram/mindmap/infographic skill families, and review contracts. Read this before producing any ProcessOn chart.
---

# ProcessOn 调用规范（WorkBuddy）

ProcessOn 的执行通道是 **MCP**：产出流程图/架构图、思维导图、信息图，并携带审阅契约。

## 1. 通道（二选一）

- **首选：本机已配置的 http 端点**。若 `~/.workbuddy/mcp.json` 已有 `processon`
  （`https://smart-hd.processon.com/mcp` + Bearer Key），直接使用，无需任何动作。
- **兜底：本插件随附的 stdio 代理** `scripts/processon_mcp_proxy.py`，在 mcp.json 里配置：

```json
"processon": {"type": "stdio", "command": "python3",
  "args": ["<插件根>/scripts/processon_mcp_proxy.py"]}
```

环境问题先读 `processon-setup` 技能。

## 2. 技能族（7 个已随插件分发）

| 技能 | 用途 |
|---|---|
| `processon-mindmap` / `processon-diagram` / `processon-infographic` | 三类产物的生产规范 |
| `processon-prompt` | 提示词口径 |
| `processon-review` | 产物审阅契约 |
| `processon-use` / `processon-setup` | 入口路由 / 环境安装 |

**做哪类图先读对应技能**；参数与验收以技能文档为准。

## 3. 纪律

- MCP 调用失败时如实报错并给上面的配置段；不编造 ProcessOn 结果。
- 产物（导图/图解/信息图）以 ProcessOn 侧可打开的实体为准，交付时给可指认的标识或链接。
- 审阅走 `processon-review` 契约，结论对应具体产物，不写空泛评语。
