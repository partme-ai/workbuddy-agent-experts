此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

# Design-System

Create a "source of truth" for your project's design language to ensure
consistency across all future screens.

> [!NOTE]
> Refer to your system prompt for instruction on handling MCP tool prefixes for
> all tools mentioned in this skill (e.g., `get_screen`,
> `create_design_system_from_design_md`, `apply_design_system`).

## 📥 Retrieval

To analyze a Stitch project, you must retrieve metadata and assets using the
Stitch MCP tools:

1. **Project lookup**: Use `list_projects` to find the target `projectId`.
2. **Screen lookup**: Use `list_screens` for that `projectId` to find
   representative screens (e.g., "Home", "Main Dashboard").
3. **Metadata fetch**: Call `get_screen` with `name: projects/{project}/screens/{screen}` to get
   `screenshot.downloadUrl` and `htmlCode.downloadUrl`.
4. **Asset download**: Use `read_url_content` to fetch the HTML code.

## 🧠 Synthesis from Description

If you need to extract a design system from existing screens, use the `stitch-design-md` skill.

If there are no existing screens (new project), or the user provides a direct description (e.g., "dark theme, blue and purple, rounded, Inter font"):

1. Map the user's vague terms to precise values using the design mappings (see `stitch-design-md` or `stitch-ui-prompt-architect`).
2. Select concrete hex codes, font families, and roundness values.
3. Generate the `DESIGN.md` file (refer to the `stitch-design-md` skill for structure).
4. Proceed to the "Create or Update Design System in Stitch" step below.

## 📝 Output Structure

The `DESIGN.md` file should follow the structure defined in the `stitch-design-md` skill.

## 🚀 Create or Update Design System in Stitch

After generating `.stitch/DESIGN.md`, make sure to also create or update the
design system in Stitch.

**Two-step design system creation:**

Check that existing authorization covers the target project, design summary and upload. Prepare those concrete details if new authorization is needed.

1. **Upload `DESIGN.md`**:
   - Read the approved `DESIGN.md`, encode it in-process, and call `upload_design_md` with the bare `projectId` plus `designMdBase64`. Do not put base64 in chat, logs, argv, or reports. The local REST helper intentionally does not accept Markdown.
2. **Create Design System**: Read the project to resolve the corresponding instance, then call `create_design_system_from_design_md` with only the current-schema `selectedScreenInstance` (`id` and `sourceScreen`).

Once the upload script and `create_design_system_from_design_md` have both completed,
Stitch holds the design tokens at the project level — you do NOT need to repeat
them in generation prompts.

## 🎨 Apply Design System to Screens

Use `apply_design_system` to apply a design system to existing screens.

> [!IMPORTANT]
> `selectedScreenInstances` must contain **only** `id` and `sourceScreen` — do
> NOT include position/dimension fields (`x`, `y`, `width`, `height`) or the
> request will fail with "invalid argument". Get the screen instance IDs from
> `get_project`.

```json
{
  "selectedScreenInstances": [
    {
      "id": "...",
      "sourceScreen": "projects/.../screens/..."
    }
  ]
}
```

**How to get the required IDs:**
1. Call `get_project` to retrieve `screenInstances` — each has an `id` and
   `sourceScreen`.
2. Call `list_design_systems` to retrieve the design system `name` (format:
   `assets/{assetId}`) — use the part after `assets/` as the `assetId`.
3. Filter out any instances with `type: "DESIGN_SYSTEM_INSTANCE"` — only pass
   real screens.

## 📋 Update Project Metadata

After writing `.stitch/DESIGN.md`, also create or update `.stitch/metadata.json`
to track the `projectId`, `title`, all known screens, and design system summary.
See [examples/metadata.json](../examples/metadata.json) for the format.

## Schema Reference

See [reference/tool-schema.md](../reference/tool-schema.md) for the full
`designSystem` object schema with all available options.

## 💡 Best Practices

Refer to the `stitch-design-md` skill for best practices on describing design elements.
