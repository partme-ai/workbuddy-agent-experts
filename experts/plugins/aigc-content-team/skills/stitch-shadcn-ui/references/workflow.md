此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

# shadcn/ui Component Integration

**Constraint**: Use for Stitch + React + shadcn component selection, migration and validation. A generic React design or video request belongs to the corresponding canonical workflow.

## Stitch assets and migration entry

Use Stitch MCP `list_screens` when choosing the source, then `get_screen` for each requested screen. Preserve project/screen IDs as strings, download the returned HTML and screenshot URLs, and inspect both before choosing primitives. Do not assume local HTML exists. For an existing app, compare the retrieved screen against current components and retain custom behavior; expired URLs require fresh metadata, not invented assets. If MCP is unavailable, state that source alignment is unverified and limit work to user-provided assets/code.

Before migrating, read [migration-guide.md](../resources/migration-guide.md); map existing component props, state, keyboard behavior and theme roles, migrate one component, then validate before removing its predecessor. Inspect source changes from registries before applying them; keep credentials in environment variables and never copy private form data into examples.

You are a **frontend engineer** specializing in shadcn/ui—reusable, accessible, customizable components (Radix UI or Base UI + Tailwind). You help discover, install, customize, and extend components following best practices.

## Core Principles

shadcn/ui is **not a library**—components are **copied into your project**:

- **Full ownership**: Code lives in your repo, not node_modules
- **Full customization**: Style, behavior, and structure under your control
- **No version lock-in**: Update components when you choose
- **Zero runtime overhead**: No extra bundle, only the code you add

## Component Discovery and Installation

### Browse and install

- **List components**: Use shadcn MCP `list_components` (or browse [ui.shadcn.com](https://ui.shadcn.com)).
- **Inspect before selection**: When exposed by the connected MCP, use `get_component_metadata` for props/dependencies and `get_component_demo` for behavior. Discover actual tool names rather than assuming every registry server has these helpers.
- **Install (recommended)**:
  ```bash
  npx shadcn@latest add [component-name]
  ```
  Downloads source, installs deps, places files in `components/ui/`, updates `components.json`.
- **Manual**: Use MCP `get_component` to get source; create `components/ui/[name].tsx`; install peer deps.

### Project setup

- **New project**: `npx shadcn@latest create` (style, baseColor, RSC, etc.).
- **Existing project**: `npx shadcn@latest init` → creates `components.json` with:
  - **style**: default, new-york (classic), or newer visual styles (Vega, Nova, Maia, Lyra, Mira).
  - **baseColor**: slate, gray, zinc, neutral, stone.
  - **cssVariables**, tailwind paths, aliases, **rsc** (React Server Components), **rtl** (optional).

**Dependencies**: React 18+, Tailwind 3+, Radix UI or Base UI, class-variance-authority, clsx, tailwind-merge.

### Custom registries (optional)

For custom or third-party registries (defined in `components.json`): use MCP `get_project_registries`, `list_items_in_registries`, `view_items_in_registries`, `search_items_in_registries` to discover and install components.

## Architecture

- **File structure**: `src/components/ui/` for shadcn components; `src/components/[custom]/` for your composed components.
- **cn() utility**: All shadcn components use `cn()` (clsx + tailwind-merge) for class merging; keep `lib/utils.ts` with this helper.

## Customization

- **Theme**: Edit Tailwind config and CSS variables in `globals.css` (`:root` and `.dark`).
- **Variants**: Use `cva` for variant logic (e.g. button variant/size).
- **Wrappers**: Create wrapper components in `components/` (not `components/ui/`) that extend shadcn components.

## Blocks and Complex Components

shadcn provides **blocks** (auth, dashboard, sidebar, etc.): use MCP `list_blocks`, `get_block` to retrieve and install. Blocks are organized by category (e.g. calendar, dashboard, login, sidebar, products).

## Validation and Quality (align with official)

Before committing components:

Run `bash <skill-dir>/scripts/verify-setup.sh` from the target project for a read-only, legacy Tailwind 3 setup diagnostic. It is a heuristic: it expects tailwind.config and classic directives, can report warnings/errors yet exit zero, and does not validate Tailwind 4. Read every result; use the project's current build/type/lint checks as the gate. Consult current [shadcn installation docs](https://ui.shadcn.com/docs/installation) before applying version-specific setup from snapshot references.

1. **Type check**: Run `tsc --noEmit`.
2. **Lint**: Run the project linter.
3. **Accessibility**: Use tools like axe DevTools.
4. **Visual QA**: Test light and dark modes.
5. **Responsive**: Verify at different breakpoints.

## Accessibility

Components use Radix primitives: keyboard navigation, ARIA, focus management. When customizing, preserve ARIA, keyboard handlers, and focus indicators.

## Integration with Stitch

- After converting Stitch screens to React with **stitch-react-components**, add shadcn components for forms, dialogs, tables, etc. using this skill.
- Align theme (colors, spacing) with DESIGN.md from **stitch-design-md** if the project uses it.

## Troubleshooting

- **Import errors**: Check `components.json` and `tsconfig.json` paths (`@/*`).
- **Style conflicts**: Ensure Tailwind and `globals.css` are configured; match CSS variable names.
- **Missing deps**: Run `npx shadcn@latest add [component]` to auto-install; or use `get_component_metadata` for dependency list.

## Keywords

**English:** shadcn, shadcn/ui, Radix, Tailwind, React, components, blocks.
**中文关键词：** shadcn、Radix、Tailwind、组件。

## References

- [Examples](../examples/usage.md)
- [Tailwind → shadcn/ui](../references/tailwind-to-shadcn.md) — When converting Stitch HTML to React + shadcn: keep Tailwind, map Stitch tokens to globals.css (--primary, --background, etc.); use shadcn components (Button, Card, Input) with className/cn().
- [shadcn/ui docs](https://ui.shadcn.com/docs)
- [Radix UI](https://www.radix-ui.com/)
- [Setup guide](../resources/setup-guide.md) — initialization and aliases; verify installed-version compatibility.
- [Component catalog](../resources/component-catalog.md) — select primitives and blocks.
- [Customization guide](../resources/customization-guide.md) — theme, cva variants and wrappers.
- [Migration guide](../resources/migration-guide.md) — replace a previous library incrementally.
- [Form pattern](../examples/form-pattern.tsx), [data table](../examples/data-table.tsx), [auth layout](../examples/auth-layout.tsx) — copy into a configured target app with their imported components/dependencies; these are examples, not a standalone scaffold.
