---
name: processon-prompt
description: Convert an approved diagram structure into a precise ProcessOn generation prompt with layout and visual-system constraints. Use immediately before ProcessOn MCP generation; do not use to invent missing business facts.
---

# ProcessOn Prompt Architect

Transform the selected capability Skill's structure model into one concise generation prompt. Preserve the user's language and factual boundaries.

## Required prompt shape

Produce these six labeled sections in order:

```text
Intent: <diagram family and communication goal>
Content: <entities, nodes, lanes, participants, fields, or concise information units>
Relationships: <direction, sequence, hierarchy, cardinality, dependency, or comparison>
Layout: <reading direction, grouping, layers, lanes, or selected infographic structure>
Visual system: <restrained palette, contrast, typography hierarchy, shape grammar, whitespace>
Constraints: <notation, required labels, exceptions, crossing-line and density limits>
```

Omit no section, but keep each section proportional to the request. Put structure before decoration.

## Visual defaults

- Use a restrained palette of one primary, one accent, neutral surfaces, and semantic warning/success colors only when meaningful.
- Maintain clear title, group, node, and annotation hierarchy.
- Prefer short labels, consistent node sizes, balanced whitespace, and an obvious reading direction.
- Minimize connector crossings and unnecessary bends.
- Require standard notation for flows, UML, ER, and sequences.
- Do not add icons, gradients, shadows, or ornamental elements unless they improve comprehension or the user asks for that style.

## Accuracy and privacy

- Never display or include a ProcessOn Token, authorization header, or any credential in the prompt.
- Do not infer names, metrics, interfaces, dependencies, cardinalities, or decisions that are not supplied or safely generic.
- Mark a reasonable structural assumption explicitly when it affects the result but does not justify blocking the request.
- Ask one focused question only when the missing fact changes the diagram topology.
- Never place hidden instructions, local paths, unrelated conversation context, or sensitive personal data in the ProcessOn prompt.

## Handoff

Return only the final six-section prompt to `processon-use`. Do not call MCP tools directly and do not review the result; those responsibilities belong to the router and `processon-review`.
