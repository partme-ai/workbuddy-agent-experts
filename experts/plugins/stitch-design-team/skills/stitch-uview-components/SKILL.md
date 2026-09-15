---
name: stitch-uview-components
description: Convert Stitch designs into uni-app and Vue 2 and uView 2.0 pages and components. Uses Stitch MCP get_screen for retrieval; high-reliability fetch via scripts; enforces uni-app page structure and uView 2 u-* component contracts.
---


# Stitch to uni-app + uView 2.0 Components

**Constraint**: Only use this skill when the user explicitly mentions "Stitch" and converting Stitch screens to **uni-app + Vue 2 + uView 2.0** (pages/, components/, .vue, u-* components).

You are a **frontend engineer** turning Stitch designs into clean, modular uni-app + uView 2 code. Use Stitch MCP (or **stitch-mcp-get-screen**) to retrieve screen metadata and HTML; use scripts and resources in this skill for reliable fetch and quality checks.

## Prerequisites

- Stitch MCP Server (https://stitch.withgoogle.com/docs/mcp/guide/)
- uni-app / HBuilderX or Vue CLI for uni-app (Vue 2)
- Stitch project and screen IDs — **two ways**: (1) From a **Stitch design URL**: parse **projectId** (path) and **screenId** (`node-id` query). (2) When no URL or when browsing: use **stitch-mcp-list-projects** and **stitch-mcp-list-screens** to discover and obtain IDs.

## Official Documentation

- **uView 2.0 (Vue 2)**: [Official](https://www.uviewui.com/) · [Guide / Demo](https://www.uviewui.com/guide/demo.html) · [Components](https://www.uviewui.com/components/intro.html) · [GitHub](https://github.com/umicro/uView2.0)
- Full links and usage: [references/official.md](references/official.md)

## Retrieval and Networking

1. **Discover Stitch MCP prefix**: Run `list_tools` to find the prefix (e.g. `mcp_stitch__stitch:`).
2. **Fetch screen metadata**: Construct `name: projects/{project}/screens/{screen}` from the string ID segments and call `[prefix]:get_screen` to get design JSON, `htmlCode.downloadUrl`, `screenshot.downloadUrl`, dimensions, deviceType.
3. **High-reliability HTML download**: AI fetch tools can fail on Google Cloud Storage URLs. Use Bash to run the skill script:
   ```bash
   bash scripts/fetch-stitch.sh "<htmlCode.downloadUrl>" "temp/source.html"
   ```
   Ensure the URL is quoted.
4. **Visual reference**: Use `screenshot.downloadUrl` to confirm layout and details.

## Architectural Rules

- **Modular pages/components**: Split the design into pages under `pages/` and shared components under `components/`; avoid one giant page.
- **Logic isolation**: Put event handlers and mixins/utils in appropriate modules.
- **Data decoupling**: Move static text, image URLs, and lists into `data/` or page data.
- **uView 2 only (use framework components when available)**: Use `u-*` components per [references/contract.md](references/contract.md). Card-like blocks → **u-cell-group** + **u-cell** or **u-text**; hints/tips → **u-text**; dividers → **u-line** / **u-divider**. Do not use view/text + custom class (.card, .card-title, .label-optional, .tips-text, .unit).
- **Project-specific**: Omit third-party license headers from generated pages/components.

## Execution Steps

1. **Environment**: Ensure uni-app project has uView 2 installed and configured (main.js, uni.scss).
2. **Data layer**: Create or update data sources (e.g. `data/mockData.js`) from the design content.
3. **Page drafting**: Use `resources/page-template.vue` as base; replace placeholder with real page name and uView 2 tags per contract.
4. **Wiring**: Register pages in `pages.json`; add tabBar or navigation as needed.
5. **Quality check**: Verify against `resources/architecture-checklist.md`; run in HBuilderX or CLI to confirm on simulator/device.

## Integration with This Repo

- **Get screen**: Use **stitch-mcp-get-screen** with projectId and screenId. Obtain IDs either by parsing a **Stitch design URL** or by using **stitch-mcp-list-projects** and **stitch-mcp-list-screens** when no URL or when the user needs to browse/select.
- **Design spec**: If Stitch was generated with **stitch-ui-design-spec-uview** constraints, map to uni-app pages and uView 2 components. If converting from Stitch HTML (e.g. get_screen htmlCode), use [references/tailwind-to-uview.md](references/tailwind-to-uview.md) for Tailwind utility → rpx/theme, then [references/contract.md](references/contract.md) for component API.
- **Design system**: If the project has DESIGN.md (from **stitch-design-md**), align colors and spacing with that system when mapping to uView tokens.

## Troubleshooting

- **Fetch errors**: Quote the URL in the bash command; ensure `scripts/fetch-stitch.sh` is executable.
- **Component mapping**: Follow [references/contract.md](references/contract.md) for layout (u-row, u-col), forms (u-form, u-input), nav (u-navbar, u-tabs), list (u-swipe-action), feedback (u-toast, u-modal).

## Keywords

**English:** Stitch, uni-app, uView, uView 2, Vue 2, u-button, u-navbar.  
**中文关键词：** Stitch、uni-app、uView、uView 2、组件。

## References

- [Examples](examples/usage.md)
- [Scripts](scripts/fetch-stitch.sh)
- [Component index (per-component doc links)](references/component-index.md)
- [Tailwind → uView 2](references/tailwind-to-uview.md) — Tailwind utility → rpx/theme when converting Stitch HTML.
- [Contract (uView 2 mapping)](references/contract.md)
- [Component API (props/events quick reference)](api/component-api.md)
- [Official documentation](references/official.md)
- [Architecture checklist](resources/architecture-checklist.md)
- [Page template](resources/page-template.vue)
- [Stitch API / MCP](https://stitch.withgoogle.com/docs/mcp/guide/)

## 能力边界

### ✅ 适用场景
- 当你需要使用此技能对应的技术栈时
- 当项目需要遵循最佳实践时
- 当需要快速上手或深入理解核心概念时

### ⚠️ 需要注意
- 复杂业务逻辑需要结合具体场景调整
- 性能优化需要根据实际数据量评估

### ❌ 不适用场景
- 不相关的技术栈或框架
- 需要完全自定义的特殊场景

## 常见陷阱 (Gotchas)

1. **版本兼容性**：注意框架版本与依赖库的兼容性，不同版本 API 可能有差异
2. **配置文件格式**：配置文件格式错误是最常见的问题，建议使用编辑器的语法检查
3. **环境变量**：确保所有必要的环境变量已正确设置，敏感信息不要硬编码
4. **依赖冲突**：多版本共存时注意依赖冲突，使用 lock 文件锁定版本
5. **性能陷阱**：大数据量场景下注意性能优化，避免 N+1 查询等常见问题

## 使用流程

### Step 1: 环境准备
确保开发环境已安装必要的依赖和工具。

### Step 2: 配置初始化
根据项目需求进行基础配置。

### Step 3: 核心功能使用
按照示例代码实现核心功能。

### Step 4: 测试验证
运行测试确保功能正常。

### Step 5: 部署上线
完成开发后进行部署和监控。
