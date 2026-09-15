---
name: stitch-uviewpro-components
description: Convert Stitch designs into uni-app and Vue 3 and uView Pro pages and components. Uses Stitch MCP get_screen for retrieval; high-reliability fetch via scripts; enforces uni-app page structure and uView Pro u-* component contracts, rpx, script setup.
---


# Stitch to uni-app + uView Pro Components

**Constraint**: Only use this skill when the user explicitly mentions "Stitch" and converting Stitch screens to **uni-app + Vue 3 + uView Pro** (pages/, components/, .vue or .uvue, u-* components).

You are a **frontend engineer** turning Stitch designs into clean, modular uni-app + uView Pro code. Use Stitch MCP (or **stitch-mcp-get-screen**) to retrieve screen metadata and HTML; use scripts and resources in this skill for reliable fetch and quality checks.

## Prerequisites

- Stitch MCP Server (https://stitch.withgoogle.com/docs/mcp/guide/)
- uni-app / HBuilderX or Vue CLI for uni-app (Vue 3)
- Stitch project and screen IDs — **two ways**: (1) From a **Stitch design URL**: parse **projectId** from path and **screenId** from `node-id` query (see **stitch-mcp-get-screen**). (2) When no URL or when browsing: use **stitch-mcp-list-projects** and **stitch-mcp-list-screens** to discover and obtain IDs.

## Official Documentation

- **uView Pro (Vue 3)**: [Official](https://uviewpro.cn/) · [Guide](https://uviewpro.cn/zh/guide/intro.html) · [Components](https://uviewpro.cn/zh/components/intro.html) · [Tools](https://uviewpro.cn/zh/tools/intro.html) · [Layout / Templates](https://uviewpro.cn/zh/layout/intro.html)
- Full links and usage: [references/official.md](references/official.md)

## Retrieval and Networking

1. **Discover Stitch MCP prefix**: Run `list_tools` to find the prefix (e.g. `mcp_stitch__stitch:`).
2. **Resolve projectId and screenId**: (1) If the user provided a **Stitch design URL**, parse **projectId** from the path (segment after `/projects/`) and **screenId** from the `node-id` query parameter. (2) Otherwise, or when the user wants to choose a project/screen, call **list_projects** (e.g. filter `view=owned`) then **list_screens** with the chosen projectId to get screenIds.
3. **Fetch screen metadata**: Construct `name: projects/{project}/screens/{screen}` from the string ID segments and call `[prefix]:get_screen` to get design JSON, `htmlCode.downloadUrl`, `screenshot.downloadUrl`, dimensions, deviceType.
4. **High-reliability HTML download**: AI fetch tools can fail on Google Cloud Storage URLs. Use Bash to run the skill script:
   ```bash
   bash scripts/fetch-stitch.sh "<htmlCode.downloadUrl>" "temp/source.html"
   ```
   Ensure the URL is quoted.
5. **Visual reference**: Use `screenshot.downloadUrl` to confirm layout and details.

## Architectural Rules

- **Modular pages/components**: Split the design into pages under `pages/` and shared components under `components/`; avoid one giant page.
- **Logic isolation**: Use `<script setup>`; put event handlers and composables in appropriate modules.
- **Data decoupling**: Move static text, image URLs, and lists into `data/` or page data.
- **uView Pro only (use framework components when available)**: Use `u-*` components **only**; do not use raw `<button>`, `<input>`, `<div>` for buttons/inputs/modals when u-* exists. Use **u-card** for cards (use `title` when only a title, or **u-section** with #right when title + right content), **u-text** for label hints and tips (type="info"/"warning", size="24"), **u-line** / **u-divider** for dividers; do not use view/text + custom class (.card, .card-title, .label-optional, .tips-text, .unit). **Tab bar must use u-tabs**; do not use custom tab-header/tab-item. **Before drafting a page, read [references/component-index.md](references/component-index.md)** and [references/contract.md](references/contract.md) for mapping rules, slot syntax (#label, #suffix, #right), and anti-patterns (Picker v-model + :range 1D; Radio value not name; no slot="...").
- **Project-specific**: Omit third-party license headers from generated pages/components.

## Execution Steps

1. **Environment**: Ensure uni-app project has uView Pro installed and configured (Vue 3, main.js, uni.scss).
2. **Data layer**: Create or update data sources (e.g. `data/mockData.js`) from the design content.
3. **Page drafting**: Follow `examples/usage.md` and the architecture checklist; draft the actual page with uView Pro tags per contract. No page-template.vue is bundled.
4. **Wiring**: Register pages in `pages.json`; add tabBar or navigation as needed.
5. **Quality check**: Verify against `resources/architecture-checklist.md`; run in HBuilderX or CLI to confirm on simulator/device.

## Official API alignment (avoid Stitch-style mistakes)

When converting Stitch HTML to uView Pro, **verify against [references/contract.md](references/contract.md) and [uView Pro docs](https://uviewpro.cn/zh/components/intro.html)**. Common corrections:

| Element | Wrong (often from Stitch/other UI) | Correct (uView Pro) |
|--------|-------------------------------------|----------------------|
| **Tab switcher** | Custom `<view class="tab-header">` + `<view class="tab-item">` | **Always use `<u-tabs :list="..." :current="..." @change="...">`**; do not build tabs with raw views/divs |
| Tabs props | `lineColor`, `activeStyle`, `inactiveStyle`, `itemStyle` | **:current**, **@change(index)** (number), **active-color**, **inactive-color** |
| Picker | `:show="show"`, `:columns="[['A','B']]"` (2D) | **v-model="show"**; **mode="selector"** + **:range** (1D array, e.g. `['A','B']`); **@confirm**; do not use :columns |
| Radio | `name="opt1"`, `customStyle`, `placement="row"` | **value="opt1"** (not name), **label** for text; no customStyle/placement |
| Slots (Vue 3) | `slot="label"`, `slot="suffix"` | **#label**, **#suffix**, **v-slot:label** — never `slot="..."` |
| Form-item label | `slot="label"` | **#label** or **v-slot:label** |
| Input type=select | — | Pair with **u-picker**; use **:select-open** bound to picker visibility |

**Pre-generation checklist** — before writing the template, ensure: (1) **Card/section** use **u-card** (with `title` or + **u-section** for title+right), not view.card + card-header + card-title. (2) **Label hints and tips** use **u-text** (type="info"/"warning", size="24"), not text with .label-optional/.tips-text/.unit. (3) **Divider** use **u-line** or **u-divider**, not view + border. (4) Tab switcher uses **u-tabs**, not custom divs. (5) All slots use **#slotname** or **v-slot:slotname**. (6) Picker uses **v-model** and **:range** (1D). (7) Radio uses **value** and **label**, not name/customStyle/placement.

## Integration with This Repo

- **Get screen**: Use **stitch-mcp-get-screen** with projectId and screenId. Obtain IDs either by parsing a **Stitch design URL** (projectId from path, screenId from `node-id`) or by using **stitch-mcp-list-projects** and **stitch-mcp-list-screens** when no URL is given or when the user needs to browse/select.
- **Design spec**: If Stitch was generated with **stitch-ui-design-spec-uviewpro** constraints, map to uni-app pages and uView Pro components. If converting from Stitch HTML (e.g. `htmlCode` from get_screen), use [references/stitch-html-patterns.md](references/stitch-html-patterns.md) for page structure and form fields; [references/tailwind-to-uviewpro.md](references/tailwind-to-uviewpro.md) for Tailwind utility → rpx/theme (spacing, typography, colors, borders, shadows); then [references/contract.md](references/contract.md) for component API and anti-patterns.
- **Design system**: If the project has DESIGN.md (from **stitch-design-md**), align colors and rpx spacing with that system when mapping to uView Pro tokens.

## Troubleshooting

- **Fetch errors**: Quote the URL in the bash command; ensure `scripts/fetch-stitch.sh` is executable.
- **Component mapping**: Use [references/component-index.md](references/component-index.md) to pick the right u-* for each element; follow [references/contract.md](references/contract.md) for layout (u-row, u-col, u-gap), forms (u-form, u-input), nav (u-navbar, u-tabs, u-tabbar), list (u-swipe-action, u-list), feedback (u-toast, u-modal, u-popup, u-empty, uni.$u). Do not substitute raw HTML for u-* components.

## Skill testing (command-triggered)

Testing is triggered by user instruction, not by calling MCP directly. Flow: user pastes the **test command** below into the chat → Agent runs this skill → resolve URL → call get_screen → fetch/parse design → generate uView Pro code → output page file or full code.

- **Test command** (paste into Cursor chat):
  ```text
  Use the Stitch skill to convert https://stitch.withgoogle.com/projects/3492931393329678076?node-id=375b1aadc9cb45209bee8ad4f69af450 into a uView Pro page
  ```
- **Expected**: Parse the two ID segments from the URL → call Stitch MCP get_screen with `name: projects/{project}/screens/{screen}` → generate uni-app + uView Pro .vue per contract and stitch-html-patterns.

## Keywords

**English:** Stitch, uni-app, uView Pro, Vue 3, u-button, u-navbar, rpx.  
**中文关键词：** Stitch、uni-app、uView Pro、组件。

## References

- **Component API**: [api/component-api.md](api/component-api.md)
- **Examples**: [examples/usage.md](examples/usage.md)
- **Contract & Patterns**:
    - [references/contract.md](references/contract.md) (Core mapping rules)
    - [references/official.md](references/official.md) (Official docs links)
    - [references/stitch-html-patterns.md](references/stitch-html-patterns.md) (HTML structure handling)
    - [references/tailwind-to-uviewpro.md](references/tailwind-to-uviewpro.md) (Style conversion)
    - [references/component-index.md](references/component-index.md) (Component list)
- **Resources**:
    - [resources/architecture-checklist.md](resources/architecture-checklist.md) (QA Checklist)
- **Scripts**:
    - [scripts/fetch-stitch.sh](scripts/fetch-stitch.sh) (High-reliability fetcher)

- **[Component index (must read)](references/component-index.md)** — Full uView Pro component list (80+) with minimal usage; consult when generating so you use u-modal, u-popup, u-action-sheet, u-empty, u-avatar, u-picker, u-tabbar, etc., instead of raw HTML.
- [Stitch HTML patterns](references/stitch-html-patterns.md) — Stitch HTML → uView Pro (page structure, forms); use when converting from get_screen htmlCode.
- [Tailwind → uView Pro](references/tailwind-to-uviewpro.md) — Tailwind utility classes → rpx / theme (spacing, typography, colors, borders, shadows); use so output is framework-native, not raw Tailwind.
- [Contract (uView Pro mapping + anti-patterns)](references/contract.md)
- [Component API (props/events)](api/component-api.md)
- [Official documentation](references/official.md)
- [Architecture checklist](resources/architecture-checklist.md)
- [Page implementation example](examples/usage.md)
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
