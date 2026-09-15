此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

## Tools

This skill is designed to call the Stitch MCP tool:

*   `generate_screen_from_text`

If your client namespaces MCP tools, it may appear as `mcp__<serverName>__generate_screen_from_text`.

## When to use this skill

**CRITICAL PREREQUISITE:**
**You must ONLY use this skill when the user EXPLICITLY mentions "Stitch".**

**ALWAYS use this skill when the user:**
- Describes a UI interface **and asks Stitch to generate it**.
- Asks to "Design", "Generate", "Create", or "Make" a screen **using Stitch**.
- Provides specific visual requirements ("Dark mode", "Blue button") for a Stitch generation.
- Wants to visualize a wireframe or concept **via Stitch**.
- Is in the **Step 5** of the `stitch-ui-designer` SOP workflow.

**Trigger phrases include:**
- "Use Stitch to design a screen" (用 Stitch 设计一个页面)
- "Stitch generate UI" (Stitch 生成 UI)
- "Draw a login page with Stitch" (用 Stitch 画一个登录页)

## Input Parameters

The skill expects you to extract the following information from the user request:

*   **`projectId`** (required): The numeric Project ID. **Format**: Pure ID (e.g., `37803...`), **NO** `projects/` prefix.
*   **`prompt`** (required): The structured text description of the screen (see "Constructing the Prompt" below).
The current live schema exposes only these two fields. If a future connected schema adds device or model fields, use only the exact values it exposes; do not reuse a historical list.

## How to use this skill

### 0. Call the MCP Tool

Invoke `generate_screen_from_text` with:

*   `projectId` (pure numeric string, no `projects/`)
*   `prompt`

### 1. Constructing the Prompt (The Art of Prompting)
The `prompt` argument is the most critical factor for quality. Do not just pass the user's raw input. You **MUST** enrich it using the **Structure Strategy**:

`[Device] [Mode] [Screen Type]. [Style]. [Layout]. [Components].`

*   **Context**: "Mobile High-Fidelity login screen."
*   **Style**: "Cyberpunk aesthetic. Dark mode. Neon blue accents."
*   **Layout**: "Center-aligned vertical stack."
*   **Components**: "Glitch-effect Logo. Input fields with glowing borders. Primary 'Jack In' button."

### 2. Describe the viewport in the prompt

Use the product targets Mobile 390x884, Tablet 768x1024, or Desktop 1280x1024 in the prompt. These are design requirements, not extra MCP arguments.

## Best Practices

1.  **Detailed Components**: Don't just say "Form". Say "Form with Email, Password, and Eye toggle icon".
2.  **Color Precision**: Mention specific colors (e.g., "Emerald Green", "#FF5733") if the user specifies them.
3.  **Content Realism**: Ask for realistic text placeholders (e.g., "Welcome back, Alice" instead of "Lorem Ipsum").
4.  **Viewport Alignment**: Ensure the prompt's layout matches the selected target dimensions.
5.  **No Code Generation**: This skill generates **Visual Designs**, not implementation code. Do not confuse with coding skills (like `uniappx-project-creator`).

## Output Handling

`generate_screen_from_text` returns session info (e.g., `sessionId` and `outputComponents`). It may not return a screenshot directly.

After the generation completes, retrieve the resulting screen(s) via:

1.  `list_screens` with the project identifier in the format required by that tool's current schema.
2.  `get_screen` with `name: projects/{project}/screens/{screen}` to fetch screenshot / HTML assets.

## Interrupted writes and deletion safety

`generate_screen_from_text`, `edit_screens` and `generate_variants` are non-idempotent writes. If a write times out or its connection is interrupted, **do not resubmit the same write call**. Reconcile the actual remote state first with `get_project`, `list_screens` and `get_screen`; issue a new write only when those reads show it is still required.

Deleting a project requires the user's explicit confirmation immediately before the delete call. Never infer deletion approval from a request to generate, edit, retry or clean up a design.

## Keywords

**English keywords:**
generate screen, design ui, create interface, make page, draw wireframe, text to ui, ui generation, stitch gen, mobile design, desktop design, dashboard, login, prompt engineering

**Chinese keywords (中文关键词):**
生成页面, 设计UI, 创建界面, 画图, 制作网页, 文本生成UI, 界面设计, 移动端设计, 桌面端设计, 仪表盘, 登录页, 线框图, 生成代码

## References

- [Examples](../examples/mobile_app.md)
- [Desktop Dashboard Example](../examples/desktop_dashboard.md)
- [Mobile App Example](../examples/mobile_app.md)
- [Wireframe Example](../examples/wireframe.md)

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
