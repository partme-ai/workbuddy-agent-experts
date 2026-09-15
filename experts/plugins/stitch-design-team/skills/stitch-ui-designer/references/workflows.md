# Workflows

## Table of contents

- Workflow overview (must follow)
- Decision points
- Execution workflow (tools available)
- Prompt-only workflow (tools unavailable)

## Workflow overview (must follow)

Follow these steps in order:

1. Preflight: detect whether Stitch MCP tools are available.
2. Classify intent: text generation, image import, existing-screen edit or variants.
3. Generate Design Spec: invoke `stitch-ui-design-spec-generator`.
4. Apply design contracts (if a named design system is present).
5. Assemble prompt: invoke `stitch-ui-prompt-architect` with `[Context] [Layout] [Components]` and the observed design-system mode. New-screen generation with an applied project-level system passes its ID separately and omits duplicate tokens; inline tokens apply to prompt-only/legacy fallback. See SKILL.md's Prompt Quality Standard.
6. Execute (tools available) or output prompt only (tools unavailable).

## Decision points

### A) Are Stitch MCP tools available?

- Yes -> follow **Execution workflow (tools available)**.
- No -> follow **Prompt-only workflow (tools unavailable)**.

### B) Is this new screen or refine/beautify?

- New screen: you may describe layout freely, but keep prompt structure stable.
- Refine/beautify: preserve layout and information architecture; avoid layout drift.

### C) Is a named design system present (e.g., uView)?

If the user request includes any of:

- `uview`, `uview2`, `uview2.0`, `u-view`

Then use `stitch-ui-design-spec-uview`.

Contract mode rules:

- If user asks for refine/beautify, or explicitly asks for selector / JSON / `contracts.include` / `states.include`:
  - Use **selector mode** (contract tool outputs selection JSON + assembled prompt).
  - Treat the selection JSON as internal; the assembled prompt is the final execution prompt.
- Otherwise:
  - Use **prefix mode** (contract tool outputs a paste-ready constraints prefix).
  - Prepend that prefix to the final prompt’s `[Context]`.

## Execution workflow (tools available)

Do not ask for confirmation loops. Execute immediately.

1. Reuse the target project or resolve it using `list_projects`; create only when needed.
2. Resolve project-level design system using `list_design_systems` and `stitch-manage-design-system` when supported.
3. Follow the intent-specific dispatch in SKILL.md: generate text, import image then edit, edit selected screen IDs, or generate variants.
4. Surface outputComponents, retrieve list_screens/get_screen assets, inspect them and update local metadata.

Output format follows SKILL.md -> Template A, including actual checks and limitations.

## Prompt-only workflow (tools unavailable)

Stop execution. Do not fake results.

1. Assemble prompt using the strict structure:
   - `[Context]`
   - `[Layout]`
   - `[Components]`
2. Output only the prompt for copy/paste.

Output format follows SKILL.md -> Template B.
