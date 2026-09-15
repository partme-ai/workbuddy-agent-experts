此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

# Code to Design

Transform your existing frontend code (React + Vite, Next.js, Angular, Vue, etc.) into a Stitch Design so you can iterate and improve it using Stitch.

This skill orchestrates three other skills in sequence:
1. `stitch-extract-static-html`: Extract a single self-contained HTML file from your build output or running dev server (e.g., Vite dev server or Angular CLI `ng serve`).
2. `stitch-extract-design-md`: Analyze the source code (including Angular `angular.json`, external `.html` templates, theme files, and components) to create a design system (DESIGN.md).
3. `stitch-upload-to-stitch`: Upload that HTML file and the design system to your Stitch project.

## Workflow

Follow these steps to convert your existing code.

### Prerequisites

- A running local dev server (e.g. `npm run dev`, `ng serve`) OR a built web application directory containing `index.html` and assets.
- Target Stitch `projectId` (use `list_projects` if unknown).

### Steps

#### 1. Extract Self-Contained HTML

Delegate to the `stitch-extract-static-html` skill to generate a standalone HTML file.
Read [skills/stitch-extract-static-html/SKILL.md](../../stitch-extract-static-html/SKILL.md) for detailed instructions and script usage.

Expected output: A single file like `/path/to/extracted/standalone.html`.

#### 2. Verify HTML

Check asset closure, route title and privacy before uploading. Offer a visual preview when available; do not claim fidelity without inspecting it.

#### 3. Extract Design System (File)

Delegate to the `stitch-extract-design-md` skill to analyze the project's source files
(components, stylesheets, theme configs) and produce a design system. Read
[skills/stitch-extract-design-md/SKILL.md](../../stitch-extract-design-md/SKILL.md) for the
full analysis workflow.

Write `.stitch/DESIGN.md` following the `stitch-extract-design-md` skill's output
structure.

#### 4. Upload DESIGN.md and Create Design System in Stitch

Delegate to the `stitch-manage-design-system` skill to upload the `DESIGN.md` and
create the design system in Stitch. Read
[skills/stitch-manage-design-system/SKILL.md](../../stitch-manage-design-system/SKILL.md) for
the full workflow (upload script usage, `create_design_system_from_design_md`
call, and required schemas). Pass
`--generated-by 'stitch-code-to-design'` when uploading.

#### 5. Upload HTML to Stitch

Use the same `stitch-upload-to-stitch` skill's script to upload the extracted HTML file.
Read [skills/stitch-upload-to-stitch/SKILL.md](../../stitch-upload-to-stitch/SKILL.md) for detailed instructions and script usage.

You will need:
- The path to the standalone HTML file generated in Step 1.
- STITCH_API_KEY available in the environment (do not print it).
- The target `projectId`.
- The `--generated-by` argument set to `'stitch-extract-static-html'`.
- The `--title` argument set to the **route path** of the page (e.g., `'/dashboard'`, `'/settings/profile'`, `'/inbox'`) so that the screen name/title in Stitch clearly identifies its route in the application.
