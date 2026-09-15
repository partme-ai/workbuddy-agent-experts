此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

# Stitch UI Prompt Architect

**Constraint**: Only use this skill when the user explicitly mentions "Stitch" or when orchestrating a Stitch design task.

This skill acts as a **Senior UX Designer** and **Prompt Engineer**. It supports two paths so that local behavior is strictly stronger than a single-path prompt skill:

- **Path A — Enhance vague prompt**: Transform rough or vague UI ideas into polished, Stitch-optimized prompts (specificity, UI/UX keywords, design system context, numbered structure). Use when the user gives a short or unclear prompt.
- **Path B — Spec → prompt**: Merge the User Request and the Design Spec (from `stitch-ui-design-spec-generator`) into a final sectioned Stitch prompt. Use when a structured spec already exists.

## Prerequisites

- **Stitch Effective Prompting Guide**: https://stitch.withgoogle.com/docs/learn/prompting/ — consult for latest best practices; they may supersede or complement the patterns below.

## Official Documentation (by Framework)

When injecting framework contract prefix (Path B) or translating component keywords, prefer the following authoritative docs:

| Framework | Official / Guide | Components | Other |
|-----------|------------------|------------|--------|
| **Bootstrap Vue 3** | [bootstrap-vue.org](https://bootstrap-vue.org) · [docs](https://bootstrap-vue.org/docs) · [Vue 3](https://bootstrap-vue.org/vue3) | [components](https://bootstrap-vue.org/docs/components) | [GitHub](https://github.com/bootstrap-vue/bootstrap-vue) |
| **Element Plus** | [element-plus.org (zh-CN)](https://element-plus.org/zh-CN/) | [design](https://element-plus.org/en-US/guide/design) · [overview](https://element-plus.org/en-US/component/overview) | [GitHub](https://github.com/element-plus/element-plus) |
| **Layui-Vue** | [layui-vue.com](https://www.layui-vue.com/zh-CN/index) | [guide](https://www.layui-vue.com/zh-CN/guide/introduce) · [components](https://www.layui-vue.com/zh-CN/components) | [GitHub](https://github.com/layui-vue/layui-vue) |
| **Vant (Vue 3)** | [vant-ui.github.io](https://vant-ui.github.io/) | [Vant zh-CN](https://vant-ui.github.io/vant/#/zh-CN) | [GitHub](https://github.com/youzan/vant) |
| **uView 2.0 (Vue 2)** | [uviewui.com](https://www.uviewui.com/) | [guide/demo](https://www.uviewui.com/guide/demo.html) · [components](https://www.uviewui.com/components/intro.html) | [GitHub](https://github.com/umicro/uView2.0) |
| **uView Pro (Vue 3)** | [uviewpro.cn](https://uviewpro.cn/) | [guide](https://uviewpro.cn/zh/guide/intro.html) · [components](https://uviewpro.cn/zh/components/intro.html) · [tools](https://uviewpro.cn/zh/tools/intro.html) · [layout](https://uviewpro.cn/zh/layout/intro.html) | — |

## When to Use

This entry writes prompts; it does not call generation tools, create projects or claim a screen was generated. In an end-to-end task, `stitch-ui-designer` invokes it as the prompt stage.

- **Path A**: User wants to polish a UI prompt before sending to Stitch; improve a prompt that produced poor results; add design system consistency to a simple idea; structure a vague concept into an actionable prompt.
- **Path B**: Orchestrator has already produced a Design Spec (e.g. from `stitch-ui-design-spec-generator`) and needs a final [Context]/[Layout]/[Components] prompt; or user requests a prompt for a named framework (uView, Element Plus, Layui, Bootstrap, Vant).

---

## Path A: Enhance Vague Prompt

Follow these steps to turn a vague idea into a Stitch-ready prompt.

### Step 1: Assess the Input

Evaluate what's missing:

| Element | Check for | If missing... |
|---------|-----------|---------------|
| **Platform** | "web", "mobile", "desktop" | Add based on context or ask |
| **Page type** | "landing page", "dashboard", "form" | Infer from description |
| **Structure** | Numbered sections/components | Create logical page structure |
| **Visual style** | Adjectives, mood, vibe | Add descriptors (see [references/KEYWORDS.md](../references/KEYWORDS.md)) |
| **Colors** | Specific values or roles | Add design system or suggest |
| **Components** | UI-specific terms | Translate to proper keywords |

### Step 2: Check for DESIGN.md

First determine the supplied execution mode. If the orchestrator confirms an applied **project-level** designSystem for new-screen generation, carry the system ID separately and output only content/layout/interactions in the prompt: no hex colors, color roles, fonts, theme or radius tokens. Keep extracted tokens in the design-system handoff. If no applied system is available (prompt-only/legacy tool fallback), use the inline DESIGN SYSTEM block below. For a targeted edit of an existing screen, include only the requested precise visual delta. Do not assume that a local DESIGN.md proves a remote system is applied.

- **If DESIGN.md exists**: Read it; extract palette, typography and component styles. Include "DESIGN SYSTEM (REQUIRED)" only in the inline-token fallback; otherwise pass tokens to the orchestrator's system handoff.
- **If DESIGN.md does not exist**: Add a tip at the end: "For consistent designs across multiple screens, create a DESIGN.md using the `stitch-design-md` skill."

### Step 3: Apply Enhancements

- **UI/UX keywords**: Replace vague terms (e.g. "menu at the top" → "navigation bar with logo and menu items"; "button" → "primary call-to-action button"). Use [references/KEYWORDS.md](../references/KEYWORDS.md) for component and adjective palettes.
- **Vibe**: Add descriptive adjectives ("modern" → "clean, minimal, with generous whitespace"; "dark mode" → "dark theme with high-contrast accents on deep backgrounds").
- **Structure**: Organize into numbered **Page Structure** (Header, Hero, Content Area, Footer, etc.).
- **Colors**: Format as `Descriptive Name (#hex) for functional role` (e.g. "Deep Ocean Blue (#1a365d) for primary buttons").

### Step 4: Format Output (Path A)

Both paths return `[Context]`, `[Layout]`, `[Components]` in that order. Platform is explicit; the layout uses numbered sections; components use concrete labels and interaction states. For the inline-token fallback, use:

```markdown
[Context]
[One-line description of the page purpose and vibe]

**DESIGN SYSTEM (REQUIRED):**
- Platform: [Web/Mobile], [Desktop/Mobile]-first
- Theme: [Light/Dark], [style descriptors]
- Background: [Color description] (#hex)
- Primary Accent: [Color description] (#hex) for [role]
- Text Primary: [Color description] (#hex)
- [Additional design tokens...]

[Layout]
**Page Structure:**
1. **[Section]:** [Description]
2. **[Section]:** [Description]
...

[Components]
[Named controls with actual UI copy and behavior]
```

**Output options**: Return as text; or if the user requests, write to `next-prompt.md` (for `stitch-loop`) or a custom file.

---

## Path B: Spec + Request → Sectioned Prompt

Use when you have a **Design Spec** (from `stitch-ui-design-spec-generator`) and a **User Request**.

### Input

- **User Request**: e.g. "Login page with social auth".
- **Design Spec**: JSON with `deviceType`, `designMode`, `theme`, `styleKeywords`, etc.

### Output Format (Must)

Return a single prompt with:

```text
[Context]
...

[Layout]
...

[Components]
...
```

### Construction Logic

**1. Context & Style**
Combine `deviceType`, `designMode`, `theme`, `styleKeywords` in the inline-token fallback. With an applied system, retain platform and purpose and send visual tokens through the system channel.
Example: "Mobile High-Fidelity login screen. Cyberpunk aesthetic. Dark mode with neon blue accents."

**2. Design Contract Prefix (Hard Constraints)**
If the user request includes a named style (e.g. "uview 风格"), select the corresponding contract. For the inline-token fallback prepend it to `[Context]`; for an applied system keep structural/component constraints in the prompt and send its visual tokens to the system handoff:

| Keyword | Use skill output as prefix |
|---------|----------------------------|
| `uview-pro`, `uviewpro` | `stitch-ui-design-spec-uviewpro` |
| `uview`, `uview2` | `stitch-ui-design-spec-uview` |
| `element`, `element-plus` | `stitch-ui-design-spec-element-plus` |
| `vant`, `vant4` | `stitch-ui-design-spec-vant` |
| `layui`, `layui-vue` | `stitch-ui-design-spec-layui` |
| `bootstrap`, `bs-vue` | `stitch-ui-design-spec-bootstrap` |

**3. Contract Selection JSON**
When a named design system is present, generate `CONTRACT_SELECTION_JSON_V1` to decide which component contracts and UI state snippets to inject (include only what the current screen needs). Schema: `version`, `designSystem`, `mode`, `contracts.include`, `states.include`.

**4. Layout Structure**
- Mobile: Header → Body (Stack) → Footer (Nav/Action).
- Desktop: Sidebar/TopNav → Main Grid → Widgets.

**5. Component Details**
Translate requirements into UI components (e.g. "Login" → Inputs, Primary Button, Forgot Pass link).

**6. Content**
Use specific copy (e.g. "Welcome back, Agent") instead of placeholder "Text".

---

## Example (Path A: Vague → Enhanced)

This example uses inline tokens because no applied project-level design system was provided.

**Input:** "make me a login page"

**Output:**

```markdown
[Context]
A clean, trustworthy login page with a centered form and subtle branding.

**DESIGN SYSTEM (REQUIRED):**
- Platform: Web, Desktop-first
- Theme: Light, minimal, professional
- Background: Clean White (#ffffff)
- Surface: Soft Gray (#f9fafb) for form card
- Primary Accent: Deep Blue (#2563eb) for submit button and links
- Text Primary: Near Black (#111827) for headings
- Text Secondary: Medium Gray (#6b7280) for labels
- Buttons: Subtly rounded (8px), full-width on form
- Cards: Gently rounded (12px), soft shadow for elevation

[Layout]
**Page Structure:**
1. **Header:** Minimal logo, centered
2. **Login Card:** Centered form with email, password fields, "Forgot password?" link
3. **Submit Button:** Primary blue "Sign In" button
4. **Footer:** "Don't have an account? Sign up" link

[Components]
Email and Password inputs with persistent labels; "Forgot password?" link;
"Sign In" primary submit action; validation errors beside the corresponding field.
```

## Targeted edit and output validation

Input: "In Stitch, add a search bar to the existing header."

```text
[Context]
Targeted edit to the existing web screen. Preserve the rest of the page.
[Layout]
1. Header: Place the search control immediately before the user avatar.
[Components]
Search input labelled "Search projects", leading magnifying-glass icon,
placeholder "Search by project name", clear action and visible focus state.
```

For an explicitly requested visual edit, add its exact value only to that control. Do not invent product claims, customer counts or private example data. Use a clear assumption when platform or copy cannot be inferred; request information only when it changes the intended result.

Before returning, check all three sections, explicit platform, numbered layout, concrete UI copy and requested behavior. Verify color name + hex + functional role in inline mode, and verify no duplicate theme tokens in an applied-system generation prompt. Missing DESIGN.md is not an error: use stated proposals and suggest `stitch-design-md` when existing assets need synthesis. Missing tools still yields prompt text without a claimed API result.

---

## Example (Path B: Spec → Prompt)

Given a mobile login Design Spec with an applied project-level system:

```text
[Context]
Mobile login screen for PayFast. The system ID is passed separately by the orchestrator.
[Layout]
1. Header: PayFast brand and "Welcome" title.
2. Form: Center-aligned vertical stack.
3. Footer: "Create Account" link.
[Components]
Email input with mail icon; Password input with visibility toggle;
full-width "Sign In" action; "Forgot Password?" link; inline validation errors.
```

---

## Tips

1. **Path choice**: Use Path A for short/vague prompts; Path B when a spec already exists or a framework name is given.
2. **Be specific early** for vague inputs; **match intent** — don’t over-design if the user wants something simple.
3. **Numbered sections** help Stitch understand hierarchy.
4. **Design system**: For multi-page consistency, use DESIGN.md (from `stitch-design-md`) or inject framework contract (Path B).
5. **Edits**: One change at a time; don’t bundle unrelated changes.

## Keywords

**English:** Stitch, prompt, enhance, vague, design spec, DESIGN.md, next-prompt, stitch-loop, uView, Element, Layui, Bootstrap, Vant.
**中文关键词：** Stitch、提示词、增强、模糊需求、设计规范、DESIGN.md、next-prompt、stitch-loop、uView、Element、Layui、Bootstrap、Vant。

## References

- [KEYWORDS](../references/KEYWORDS.md) — UI/UX keyword palettes for Path A.
- [Official documentation (by framework)](#official-documentation-by-framework) — Authoritative docs for BootstrapVue, Element Plus, Layui-Vue, Vant, uView 2, uView Pro.

- [Examples](../examples/usage.md)
- [Keywords](../references/KEYWORDS.md)
