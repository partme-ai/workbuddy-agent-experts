此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

# Stitch Designer (Master Skill)

This is the execution entry point for Stitch design tasks. It coordinates the existing spec, contract and prompt skills before calling Stitch MCP.

## When to use this skill

**CRITICAL PREREQUISITE:**
**You must ONLY use this skill when the user EXPLICITLY mentions "Stitch" in their request.**

**Use this skill when:**
- The user asks to "Design a UI", "Create a screen", "Make an app page" **using Stitch**.
- The user provides a high-level design request (e.g., "I need a dashboard for my SaaS") **and mentions Stitch**.

**Trigger phrases include:**
- "Use Stitch to design..."
- "Stitch me a UI for..."

## Workflow (Flow-first, copy-pastable)

This skill must follow this workflow end-to-end. Do not skip steps.

### 0) Preflight (Tool Availability)

1. Detect whether Stitch MCP tools are available.
2. If tools are available, follow the **Execution workflow**.
3. If tools are not available, follow the **Prompt-only workflow**.

### 1) Intent Classification

Determine the task type:

- **New screen**: design + generate a new UI screen.
- **Refine / Beautify**: modify an existing screen while preserving layout and information architecture.
- **Image / mockup**: import with `stitch-upload-to-stitch`, then refine the returned screen using `edit_screens`.
- **Variants**: use `stitch-ui-design-variants` for variant planning and the available `generate_variants` tool for actual generation.

### 2) Design Spec Workflow (Brain)

Invoke `stitch-ui-design-spec-generator` with the user request.

Expected result:

- A structured `Design Spec` JSON (Theme, Device, Style, Mode).

### 3) Contract Workflow (Hard Constraints)

If the request includes a named design system / style, fetch constraints from the matching design contract tool and inject them into the final prompt.

Supported mapping (Match Priority: Specific > General):

- `uview-pro`, `uviewpro`, `uview pro` -> use `stitch-ui-design-spec-uviewpro` (Match this FIRST)
- `uview`, `uview2`, `uview2.0`, `u-view` -> use `stitch-ui-design-spec-uview`
- `layui`, `layui-vue`, `layui vue` -> use `stitch-ui-design-spec-layui`
- `bootstrap`, `bootstrap-vue`, `bs-vue` -> use `stitch-ui-design-spec-bootstrap`
- `element`, `element-plus`, `el-plus`, `element-ui` -> use `stitch-ui-design-spec-element-plus`
- `vant`, `vant4`, `vant-ui` -> use `stitch-ui-design-spec-vant`

Decision rules:

- If the user asks for refine/beautify, or explicitly asks for selector / JSON / `contracts.include` / `states.include`:
  - Use `stitch-ui-design-spec-uview` or `stitch-ui-design-spec-layui` in **selector mode**.
  - Treat the returned selection JSON as internal and use the assembled prompt as the execution prompt.
- Otherwise:
  - Use `stitch-ui-design-spec-uview` or `stitch-ui-design-spec-layui` in **prefix mode**.
  - Prepend the returned prefix to `[Context]`.

### 4) Prompt Assembly Workflow (Pen)

First resolve the target project (reuse the supplied ID or use `list_projects`; create only when a new workspace is needed). Discover `list_design_systems`: if a system is applied, pass its `designSystem` ID separately from the prompt. If no system exists and the tools support it, use `stitch-manage-design-system` to establish the requested tokens before generating. Pass the observed design-system state and intended mode to the prompt architect.

For **new-screen generation with an applied project-level system**, the execution prompt contains platform, content, layout and interactions; remove color/font/theme/radius tokens from framework prefixes and DESIGN.md text. For **prompt-only or legacy tools without design-system support**, retain the explicit token block described below and label the fallback. For **targeted edits**, precise requested color adjustments are allowed. Do not silently replace an existing project's design system.

Invoke `stitch-ui-prompt-architect` with the user request and (if any) Design Spec + contract prefix. The output must conform to **Prompt Quality Standard: Optimized Prompt Structure** (see below) so that Stitch receives a precise "construction blueprint" rather than a vague idea.

**Minimum structure** (always present):

```text
[Context]
...

[Layout]
...

[Components]
...
```

**When the request describes an app or multi-section screen**, keep Project Overview and Page Structure and Function. The Design System block below applies to the inline-token fallback; with a project-level system, carry its ID as tool metadata instead.

### 5) Execution Workflow (Hand) — Tools Available

ALWAYS execute immediately (no confirmation loop):

1. Resolve/reuse project and applicable design system, then assemble the prompt through `stitch-ui-prompt-architect`.
2. Dispatch by intent: `generate_screen_from_text` for text; `stitch-upload-to-stitch` then `edit_screens` for an image; `edit_screens` for existing screen adjustments; `generate_variants` for requested alternatives. Preserve screen IDs as strings. Use `deviceType` `MOBILE`, `DESKTOP` or `TABLET` from the brief/metadata; inspect the connected tool schema before passing optional fields.
3. For edits/variants, resolve `selectedScreenIds` using `list_screens`/`get_screen` before mutation. For variants, the pinned upstream supports `variantCount` 1–5, `creativeRange` REFINE/EXPLORE/REIMAGINE and aspects LAYOUT/COLOR_SCHEME/IMAGES/TEXT_FONT/TEXT_CONTENT; use only values accepted by the live tool.
4. Surface returned `outputComponents` text descriptions and suggestions. List screens and call `get_screen` to verify actual screen IDs and retrieve screenshot/HTML; do not assume local HTML exists.
5. Download returned assets to the target `.stitch/designs` with screen-ID/slug filenames; preserve useful previous versions. Inspect actual screenshots against requested layout, copy, device and constraints. Use focused edits for a local mismatch; regenerate only when the fundamental layout is wrong.
6. Update `.stitch/metadata.json` with returned IDs, device types, system information and sync time. Report what was actually generated, downloaded and visually checked. On tool failure, preserve prior assets, report the error and stop dependent calls.
7. Treat `generate_screen_from_text`, `edit_screens` and `generate_variants` as non-idempotent writes. If one times out or the connection drops, **do not submit the same write call again**. First reconcile remote state with all three read probes: `get_project`, `list_screens` and `get_screen`. If `list_screens` returns no candidate screen, record that `get_screen` could not be called and why; do not silently treat the probe as optional. Only make a new write after the observed state proves it is still needed.
8. Deleting a Stitch project is destructive. Obtain the user's explicit confirmation immediately before the delete call; an earlier request to design, edit or clean up is not confirmation to delete.

### 6) Prompt-only Workflow — Tools Not Available

STOP execution. Do not fake results. Output only a copy-paste prompt for the user to run in Stitch.

## Output Patterns (Strict Templates)

Use these templates to keep outputs consistent.

### Template A — Tools Available (Execution Report)

ALWAYS use this exact template:

```markdown
# Stitch Design Delivery

## Execution Result
- Project: projects/{id}
- Screen: {screenId}

## Asset Export
- Screenshot: {from get_screen output}
- HTML: {from get_screen output}

## Notes
- Prompt: Executed with `[Context] [Layout] [Components]` structure (including required constraints and layout invariants).
```

### Template B — Tools Not Available (Prompt Only)

ALWAYS use this exact template. When the request is app/product-level or multi-section, the **content** inside each section must follow the **Optimized Prompt Structure** (Project overview in Context; Design system (required) in Context or a dedicated block; Page structure and function with core function + areas in Layout/Components).

```text
[Context]
...

[Layout]
...

[Components]
...
```

## Prompt Quality Standard: Optimized Prompt Structure

To make Stitch **accurately** implement the design, the final prompt (from step 4) must be a **detailed construction blueprint**, not a short wishlist. Use the following structure whenever the user describes an app, a product, or a screen with multiple sections.

**Source of truth**: This structure is derived from the optimized-prompt pattern: a clear **project overview**, a **design system (required)** with explicit tokens, and **page structure and function** with one **core function** per page/section plus **area-level details** (top nav, main visual, function area, actions, bottom). Reference: blog "Trae+Stitch MCP+Skills: My New AI Programming Paradigm" — after optimization it becomes a detailed construction blueprint including color scheme, font sizes, button styles, page layout, and UX.

### 1) Project Overview — Required for app/product-level requests

- One short paragraph: **what** the product/screen is, **who** it is for, **style** (e.g. modern minimal, professional and trustworthy, bright and fresh), and **key attributes** (ease of use, information readability, full localized UI, etc.).
- Example: "An AI ingredient-list analysis tool for end users, turning chemical terms into plain language via image recognition and composition parsing. Modern minimal design, emphasis on ease of use and readability, full localized interface."

### 2) Design System — Inline-token fallback only

When no applied project-level system is available, the prompt includes an explicit design system block. When a system is applied, send its ID and omit this token block from new-screen generation. For the fallback, include:

| Block | Content | Example |
|-------|---------|--------|
| **Platform** | Web / Mobile / Desktop, target device or width | "Mobile miniapp, prioritize iOS and Android" / "Admin Web, min width 1280px" |
| **Theme** | Mood + domain affinity | "Bright and fresh, professional and trustworthy, with domain-friendly tone" |
| **Color scheme** | Primary + Secondary + Warning + Neutrals (Background, Text, Secondary text, Divider), each with **#hex** and usage | Primary #165DFF for buttons/nav; Secondary #36D399 for positive cues; Background #FFFFFF; Text #1D2129; Secondary text #86909C; Divider #F2F3F5 |
| **Typography** | Title / Body / Auxiliary: **size (px)** + **font** + **weight** | Title 20px Bold; Body 16px Regular; Auxiliary 14px Light |
| **Component style** | Buttons / Cards / Icons: radius, shadow, interaction | Buttons 8px radius, soft shadow; Cards 12px radius, light shadow; Icons linear, minimal |

If a **named design system** (uView Pro, Bootstrap, Element Plus, etc.) is used, the contract prefix from step 3 already supplies tokens; the assembled prompt must still state **Platform**, **Theme**, and **Layout invariants** in human-readable form so Stitch understands intent.

### 3) Page Structure and Function

For **each** page or major section:

- **Core function**: One line — "This page/section is for... so that..."
- **Areas** (choose as needed): **Top nav** / **Hero / main visual** / **Function area** / **Action area** / **Footer** / **Sidebar**.
- Under each area: **concrete elements** (e.g. "Brand logo + Help entry", "Primary CTA 'Scan label' large filled", "Secondary 'Choose from gallery' outline"). Use specific copy and roles (primary button, secondary button, card, list item) instead of "a button" or "some text".

**Example (single section):**

```text
### 1. Home (Scan / Upload)
**Core function**: App entry, guide user to start
- **Top nav**: Brand logo + Help entry
- **Hero**: Headline "Ingredient Translator" + subhead "Understand food labels at a glance"
- **Function area**: Primary button "Scan label" (large, primary fill); Secondary "Choose from gallery" (outline, primary border); short usage copy
- **Footer**: Privacy and terms links
```

### 4) Prompt Structure Checklist (before calling generate_screen_from_text)

Verify (and if missing, request the prompt-architect to add):

- [ ] **Project overview** present for app/product-level requests? (one paragraph: what, who, style, key attributes)
- [ ] **Design-system delivery** correct? Applied project-level system: ID sent, no duplicate tokens in new-screen prompt. Inline fallback: Platform, Theme, **Color scheme with #hex**, **Typography (px + font + weight)** and **Component style** present.
- [ ] **Per-page/section**: **Core function** one line + **areas** (top nav / hero / function / action / footer) with **concrete elements** and specific copy?
- [ ] **Layout** and **Components** sections still populated? (macro layout + component list)
- [ ] No vague placeholders? ("a button" → "primary CTA button 'Sign In'"; "some list" → "vertical list of Workout Cards with thumbnail, duration, Start button")

If a required field is missing, **re-invoke** `stitch-ui-prompt-architect` with the observed delivery mode and missing field, then re-run the checklist before execution.

---

## Anti-Patterns (Strict Prohibitions)
*   ⛔ **NO FAKE SUCCESS**: If you didn't get a real API response, do not say "Project Created".
*   ⛔ **NO APP SCAFFOLDING**: Do not invoke any external project scaffolding skills (e.g., `uniappx-project-creator`, `flutter-project-creater`, `react-native-project-creater`) and do not run scripts to create codebases.
*   ⛔ **NO CODING**: Do not write Vue/React/HTML code in this flow. This skill is for **Design Generation** only.
*   ⛔ **NO CONFUSION**: A "Stitch Project" is a design workspace, NOT a code repository.

## Keywords
orchestrator, design agent, ui designer, master skill, design flow, stitch pilot

## References

- [Design mappings](../references/design-mappings.md) and [prompt keywords](../references/prompt-keywords.md) — choose precise component terms; apply visual descriptors only in the appropriate design-system/edit channel.
- [Enhanced prompt](../examples/enhanced-prompt.md) — project-level system example with the canonical three sections.

- [Workflow End-to-End](../examples/workflow_end_to_end.md)
- [Workflows Reference](../references/workflows.md)
- [Optimized Prompt Output Examples (ZH + EN)](../examples/optimized_prompt_output_examples.md) — full Chinese and English examples of the optimized prompt (project overview + design system + page structure and function) from the blog "Trae+Stitch MCP+Skills: My New AI Programming Paradigm".
- **Optimized prompt structure**: Project Overview + Design System (required) + Page Structure and Function. See blog "Trae+Stitch MCP+Skills: My New AI Programming Paradigm" (optimized prompt section). Goal: turn a vague idea into a detailed construction blueprint (colors, font sizes, button styles, layout, UX) to improve Stitch output precision.

## 国内适配

- 支持中文文档和中文注释
- 示例代码兼容国内开发环境
- 提供中文 FAQ 和常见问题解答
