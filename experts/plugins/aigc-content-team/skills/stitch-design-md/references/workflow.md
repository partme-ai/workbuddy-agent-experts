此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

# Stitch DESIGN.md

**Constraint**: Only use this skill when the user explicitly mentions "Stitch" or when preparing design system docs for Stitch generation.

You are an expert **Design Systems Lead**. Your goal is to analyze Stitch project assets and synthesize a **Semantic Design System** into a file named `DESIGN.md`.

## Overview

`DESIGN.md` is the **source of truth** for prompting Stitch to generate new screens that match existing design language. Stitch interprets design through visual descriptions and specific color values. This skill uses **Stitch MCP** to fetch project and screen data; you can call `stitch-mcp-list-projects`, `stitch-mcp-list-screens`, `stitch-mcp-get-screen`, `stitch-mcp-get-project` (or the underlying MCP tools with your client’s prefix) to retrieve metadata and download HTML/screenshots.

## Prerequisites

- Stitch MCP Server configured (see https://stitch.withgoogle.com/docs/mcp/guide/)
- A Stitch project with at least one designed screen
- Alternatively, user-provided local code/HTML and visual assets whose design should be documented; this path does not require a Stitch project.
- Stitch Effective Prompting Guide: https://stitch.withgoogle.com/docs/learn/prompting/

## Retrieval and Networking

### When the source is local code/HTML

Read the provided markup, CSS/Tailwind configuration and representative screenshots. Record `Source` with repo-relative paths and revision when available; record which values are observed and which are proposed. Do not invent a Project ID or claim MCP retrieval. If only code is available, label visual atmosphere as inferred and request/produce an authorized preview before claiming visual confirmation. For precise CSS extraction, use `stitch-extract-design-md`; this entry owns semantic synthesis and validation. Publishing project-level tokens belongs to `stitch-manage-design-system`.

Use Stitch MCP (or skills `stitch-mcp-list-projects`, `stitch-mcp-get-project`, `stitch-mcp-list-screens`, `stitch-mcp-get-screen`) in this order.

### When the user provides a Stitch design URL

If the user pastes a **Stitch design page link** (e.g. `https://stitch.withgoogle.com/projects/3492931393329678076?node-id=375b1aadc9cb45209bee8ad4f69af450`):

1. **Parse the URL**:
   - **projectId** = segment after `/projects/` and before `?` (e.g. `3492931393329678076`)
   - **screenId** = query parameter `node-id` (e.g. `375b1aadc9cb45209bee8ad4f69af450`)
2. **Fetch the screen**: Construct `name: projects/{project}/screens/{screen}` from the parsed string segments and call `[prefix]:get_screen` (no list call is needed).
3. **Continue** with step 5 below (asset download) and then Analysis & Synthesis.

### When project/screen IDs are unknown

1. **Namespace discovery**: Run `list_tools` to find the Stitch MCP prefix (e.g. `mcp_stitch__stitch:`). Use that prefix for all calls.

2. **Project lookup** (if Project ID unknown):
   - Call `[prefix]:list_projects` with `filter: "view=owned"`
   - Identify the target project by title; extract Project ID from `name` (e.g. `projects/13534454087919359824`)

3. **Screen lookup** (if Screen ID unknown):
   - Call `[prefix]:list_screens` with `projectId` (numeric ID only)
   - Identify target screen by title; extract Screen ID from `name`

4. **Metadata fetch**:
   - Construct `name: projects/{project}/screens/{screen}` from the exact returned ID strings and call `[prefix]:get_screen`
   - Use returned `screenshot.downloadUrl`, `htmlCode.downloadUrl`, `width`, `height`, `deviceType`, and project `designTheme`. Preserve IDs as strings rather than coercing hexadecimal screen IDs to numbers; do not assume cached HTML is current.

5. **Asset download** (also after URL-based get_screen):
   - Use `web_fetch` or equivalent to download HTML from `htmlCode.downloadUrl` and optionally screenshot from `screenshot.downloadUrl`
   - Parse HTML for Tailwind classes, custom CSS, and component patterns

6. **Project metadata**:
   - Call `[prefix]:get_project` with project `name` (full path `projects/{id}`) to get `designTheme`, fonts, roundness, custom colors, layout principles

## Analysis & Synthesis

### 1. Extract Project Identity
- Project title and Project ID (from JSON `name`)

### 2. Define the Atmosphere
From screenshot and HTML: mood, density, aesthetic (e.g. "Airy," "Minimalist," "Utilitarian").

### 3. Map the Color Palette
For each key color:
- Descriptive name (e.g. "Deep Muted Teal-Navy")
- Hex in parentheses (e.g. "#294056")
- Functional role (e.g. "Used for primary actions")

### 4. Translate Geometry & Shape
- `rounded-full` → "Pill-shaped"
- `rounded-lg` → "Subtly rounded corners"
- `rounded-none` → "Sharp, squared-off edges"

### 5. Describe Depth & Elevation
Shadows and layers: "Flat," "Whisper-soft diffused shadows," "Heavy drop shadows," etc.

## Output Guidelines

- **Language:** Descriptive design terminology and natural language only
- **Format:** Markdown following the structure below
- **Precision:** Exact hex codes plus descriptive names
- **Context:** Explain the "why" behind design decisions

## Output Format (DESIGN.md Structure)

```markdown
# Design System: [Project Title]
**Project ID:** [Insert Project ID Here]

## 1. Visual Theme & Atmosphere
(Description of mood, density, and aesthetic philosophy.)

## 2. Color Palette & Roles
(Descriptive Name + Hex + Functional Role for each color.)

## 3. Typography Rules
(Font family, weights for headers vs body, letter-spacing.)

## 4. Component Stylings
* **Buttons:** Shape, color, behavior.
* **Cards/Containers:** Corner roundness, background, shadow.
* **Inputs/Forms:** Stroke style, background.

## 5. Layout Principles
(Whitespace, margins, grid alignment.)

## 6. Design System Notes for Stitch Generation
(Language and color references to copy into Stitch prompts; see examples/DESIGN.md.)
```

For local sources, replace the Project ID line with `**Source:**` and actual source paths. Template brackets are instructions, not permitted final output. Keep Section 6 as the local reusable prompt contract in addition to the official five-section structure.

## Validation / lint

This snapshot of official `design-md` provides a structure and semantic constraints, but no lint executable. Apply these local lint checks before delivery:

1. Sections 1–5 are populated: atmosphere, palette/roles, typography, component styling, layout. Section 6 preserves reusable generation notes.
2. Every color has a descriptive name, actual hex value and functional role; font weights, spacing, radii and shadows agree with cited source assets. Translate implementation classes into visual language.
3. Document source paths or real project/screen IDs and observation limits. No invented tokens, credentials, signed download URLs, empty placeholders or claimed visual QA without an inspected image.
4. Compare buttons/cards/inputs and responsive navigation against representative screens. Distinguish observed behavior from suggested hover/focus or breakpoint values.
5. Read the completed DESIGN.md as input to `stitch-ui-prompt-architect`: verify it can recover palette roles and layout invariants without source code. A missing role, conflicting token or unexplained source difference fails lint; resolve it before claiming completion.

On asset retrieval failure, preserve existing DESIGN.md, report the missing evidence and emit a clearly marked partial draft. Local lint is not proof of live rendering or accessibility compliance.

## Integration with This Repo

- **First time:** Generate `DESIGN.md` with this skill from an existing Stitch screen.
- **Multi-page:** Use `stitch-ui-prompt-architect` to inject DESIGN.md Section 6 into prompts; use `stitch-loop` for baton-based multi-page builds.
- **Framework alignment:** For framework-specific constraints (Layui, Element Plus, uView, etc.), combine DESIGN.md with the corresponding `stitch-ui-design-spec-*` contract in the prompt.

## Best Practices

- **Be descriptive:** e.g. "Ocean-deep Cerulean (#0077B6)" not "blue"
- **Be functional:** Explain what each element is used for
- **Be consistent:** Same terminology throughout
- **Be precise:** Exact values in parentheses after natural language

## Common Pitfalls

- ❌ Technical jargon without translation ("rounded-xl" → "generously rounded corners")
- ❌ Omitting color codes or only descriptive names
- ❌ Skipping functional roles of design elements
- ❌ Vague atmosphere descriptions
- ❌ Ignoring shadows or spacing patterns

## Keywords

**English:** DESIGN.md, design system, Stitch, color palette, typography, layout.
**中文关键词：** DESIGN.md、设计系统、Stitch、色彩、排版、布局。

## References

- [Examples](../examples/usage.md)
- [Example DESIGN.md](../examples/DESIGN.md) — Full sample output
- [Stitch Prompting Guide](https://stitch.withgoogle.com/docs/learn/prompting/)
