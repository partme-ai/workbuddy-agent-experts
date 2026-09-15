此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

# Stitch to React Components

**Constraint**: Only use this skill when the user explicitly mentions "Stitch" and converting Stitch screens to React (Vite/React, TypeScript).

You are a **frontend engineer** turning Stitch designs into clean, modular React code. Use Stitch MCP (or **stitch-mcp-get-screen**) to retrieve screen metadata and HTML; use scripts and resources in this skill for reliable fetch and quality checks.

## Prerequisites

- Stitch MCP Server (https://stitch.withgoogle.com/docs/mcp/guide/)
- Node.js and npm (for Vite/React project and optional validation)
- Stitch project and screen IDs — **two ways**: (1) From a **Stitch design URL**: parse **projectId** (path) and **screenId** (`node-id` query). (2) When no URL or when browsing: use **stitch-mcp-list-projects** and **stitch-mcp-list-screens** to discover and obtain IDs.

## Retrieval and Networking

1. **Discover Stitch MCP prefix**: Run `list_tools` to find the prefix (e.g. `mcp_stitch__stitch:`).
2. **Fetch screen metadata**: Use `list_screens` with a bare project ID, then call `[prefix]:get_screen` for each with `name: projects/{project}/screens/{screen}`. Preserve both ID segments as strings. Obtain `htmlCode.downloadUrl`, `screenshot.downloadUrl`, dimensions and deviceType.
3. **High-reliability HTML download**: AI fetch tools can fail on Google Cloud Storage URLs. Use Bash to run the skill script:
   ```bash
   bash scripts/fetch-stitch.sh "<htmlCode.downloadUrl>" "temp/source.html"
   ```
   This uses `curl -L` for redirects and TLS. Ensure the URL is quoted.
4. **Visual reference**: Use `screenshot.downloadUrl` to confirm layout and details.
5. **Sync provenance**: For each requested screen, store HTML and screenshot under the target app's `.stitch/designs/`; preserve existing assets unless refresh is authorized. Use cached assets only when their provenance matches and reuse is intended. On Google image URLs supporting sizing, request `=w{width}` from returned metadata and inspect the actual image dimensions. Fetch `get_project`; update the app's `.stitch/metadata.json` with projectId, title, deviceType, `Last Sync Time` (ISO time), and a screens map (ID, label, sourceScreen, dimensions, canvasPosition). Mirror only within an authorized workspace.

## Architectural Rules

- **Modular components**: Split the design into separate files; avoid one giant file.
- **Logic isolation**: Put event handlers and business logic in `src/hooks/`.
- **Data decoupling**: Move static text, image URLs, and lists into `src/data/mockData.ts`.
- **Type safety**: Every component must have a `Readonly` TypeScript interface `[ComponentName]Props`.
- **Project-specific**: Do not add unrelated license headers to new code; retain required notices when adapting upstream source.
- **Style mapping**: Extract `tailwind.config` from HTML `<head>`; sync with `resources/style-guide.json` if present; use theme-mapped Tailwind classes instead of raw hex.
- **Fresh tokens**: The bundled style-guide is an example, not the project's palette. Extract colors, fonts, spacing, radii and typography into a project-local style-guide; verify it against this project's HTML and DESIGN.md before drafting. Preserve the installed Skill resources.
- **Navigation**: Replace placeholder `href="#"` with React Router `<Link>` routes (or the existing router's equivalent). Make the top-bar logo/title a home link; wire sidebar and bottom navigation with active states. Check desktop home navigation when mobile bottom bars use `md:hidden`.
- **Dark mode**: Where the target supports dark mode, map every color role to matching `dark:` variants; verify both themes instead of copying fixed sample colors.

## Execution Steps

1. **Environment**: If the project has no `node_modules`, run `npm install` so validation (if used) works.
2. **Data layer**: Create `src/data/mockData.ts` from the design content.
3. **Component drafting**: Use `resources/component-template.tsx` as base; replace all `StitchComponent` with the real component name.
4. **Wiring**: Update the app entry (e.g. `App.tsx`) to render the new components.
5. **Quality check**: Use the bundled [AST validator](../scripts/validate.js): install its locked dependencies with `npm ci --prefix <skill-dir>`, then `node <skill-dir>/scripts/validate.js <absolute-component.tsx>` for each component/page. It checks parseability, a Props interface, and literal className hex values; it does not prove Readonly use, routing or visual correctness. Run the target project's TypeScript check (`tsc --noEmit` through its installed toolchain), [architecture checklist](../resources/architecture-checklist.md), and proportional visual checks. Report skipped checks explicitly.

## Integration with This Repo

- **Get screen**: Use **stitch-mcp-get-screen** (or MCP `get_screen`) with `name: projects/{project}/screens/{screen}`. Obtain the ID segments from a Stitch URL or the list Skills.
- **Design system**: If the project has DESIGN.md (from **stitch-design-md**), align colors and typography with that semantic system when mapping to Tailwind. When converting Stitch HTML to React, use [references/tailwind-to-react.md](../references/tailwind-to-react.md) for theme-mapped Tailwind (tokens → tailwind.config); keep Tailwind classes in output, map Stitch tokens to project theme.

## Troubleshooting

- **Fetch errors**: Quote the URL in the bash command to avoid shell issues; ensure `scripts/fetch-stitch.sh` is executable.
- **Validation errors**: Fix missing Props interfaces and hardcoded styles per the AST report; follow [resources/architecture-checklist.md](../resources/architecture-checklist.md).

## Keywords

**English:** Stitch, React, Vite, components, validation, mockData, Tailwind.
**中文关键词：** Stitch、React、组件、校验、Tailwind。

## References

- **Examples**: [examples/usage.md](../examples/usage.md)
- **Style Mapping**: [references/tailwind-to-react.md](../references/tailwind-to-react.md) — Theme-mapped Tailwind when converting Stitch HTML; keep Tailwind classes, sync Stitch tokens to tailwind.config.
- **Resources**:
    - [resources/architecture-checklist.md](../resources/architecture-checklist.md)
    - [resources/component-template.tsx](../resources/component-template.tsx)
- **Scripts**: [scripts/fetch-stitch.sh](../scripts/fetch-stitch.sh)
- **API and sync mapping**: [resources/stitch-api-reference.md](../resources/stitch-api-reference.md)
- **Component example**: [examples/gold-standard-card.tsx](../examples/gold-standard-card.tsx) — adapt routes and project tokens before use; structural AST success alone is insufficient.
- [Stitch API / MCP](https://stitch.withgoogle.com/docs/mcp/guide/)
