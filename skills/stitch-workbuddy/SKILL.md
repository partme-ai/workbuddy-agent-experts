---
name: stitch-workbuddy
description: How to reach Google Stitch from WorkBuddy - MCP stdio proxy setup, tool families (create-project / generate-screen-from-text / list / get), screen download conventions, and the design-to-markdown delivery flow. Read this before any Stitch design task.
---

# Google Stitch 调用规范（WorkBuddy）

Stitch 的执行通道是 **MCP**：本插件随附 `scripts/stitch_mcp_proxy.py`（stdio 代理），指向 Google Stitch 的 MCP 服务。

## 1. 一次性配置（用户没配就先引导配置）

在 `~/.workbuddy/mcp.json` 的 `mcpServers` 里加（路径换成本插件实际安装路径，通常在
`~/.workbuddy/plugins/cache/my-experts/stitch-design-team/<版本>/` 或 marketplaces 目录下）：

```json
"stitch": {
  "type": "stdio",
  "command": "python3",
  "args": ["<插件根>/scripts/stitch_mcp_proxy.py"]
}
```

配置后重启 WorkBuddy 生效。凭据（STITCH_API_KEY）注入方式：mcp.json 的 `env` 字段即可；
上游 `stitch-local-setup` 技能面向 Codex 宿主，其凭据安全原则（Key 不进 Git/插件目录、权限收紧）同样适用。

## 2. 工具族（技能里教的流程都以这些工具落地）

| 工具族 | 用途 |
|---|---|
| `create-project` / `list-projects` / `get-project` | 项目管理（`projectId` 是后续一切的锚点） |
| `generate-screen-from-text` | 文本生成界面（`list_screens` 用纯 `projectId`；`get_screen` 要完整 `name:`） |
| 屏幕下载 | 官方下载域为 `lh3.googleusercontent.com` 与 `contribution.usercontent.google.com` |

**实测约束**（来自上游验证记录，别踩）：`deviceType` 传 TABLET 可能被服务端按 DESKTOP 执行
（返回以实际为准，不要按请求值假设）；尺寸是 **2× 设备像素**；设备/尺寸在 `get_screen`
**顶层**而非 `screenInstance`。

## 3. 交付流

1. `create-project` → 记下 `projectId`。
2. `generate-screen-from-text` 生成屏幕（一屏一屏来，别一把梭）。
3. `get_screen` 拉详情 → 下载素材 → 用 `stitch-design-md` 规范产出门面设计 Markdown。
4. 需要落地代码时走 `stitch-code-to-design` / `stitch-extract-static-html`。
5. 交付前过 `stitch-delivery-harness`（或 design-qa 清单）。

## 4. 纪律

- 全部 43 个 `stitch-*` 技能已随插件分发：**做哪类任务先读对应技能**，工具参数以技能文档为准。
- MCP 未配置/调用失败时，如实报错并给出上面的配置段，不要凭空编造 Stitch 结果。
- 产物路径与下载链接原样进汇报，不做未经请求的转存。
