---
name: processon-mindmap
description: Convert text, documents, plans, and knowledge into a concise ProcessOn mind map, logic map, organization map, fishbone, timeline, WBS tree, or tree table. Use for hierarchical knowledge and structured understanding, not process or interaction diagrams.
---

# Mind-Map Modeling

Produce a faithful, browsable hierarchy before handing it to `processon-prompt`. One node communicates one idea.

## Structure selection

| Structure | Use when |
|---|---|
| `mind_free` | Central topic, brainstorming, broad knowledge classification |
| `mind_right` | Linear outline, learning path, proposal, ordered reasoning |
| `mind_org` | Department, role, reporting, or genealogy hierarchy |
| `mind_ishikawa_left` | Root-cause analysis and contributing factors |
| `mind_timeline_h` | Milestones, history, roadmap, or staged evolution |
| `mind_tree_free` | WBS, deliverable decomposition, taxonomy |
| `mind_treeTable_left_title` | Comparable attributes, parameter inventory, structured classification table |

These identifiers are ProcessOn structure concepts, not current MCP parameters. The official MCP tool accepts only `prompt`; express the selected structure in that prompt without inventing a field.

## Content transformation

1. Identify one root topic from the user's objective and source material.
2. Preserve authoritative headings and their parent-child relationships.
3. Merge duplicates and separate genuinely independent branches.
4. Condense leaf content to one short claim, fact, action, or question.
5. Keep hierarchy continuous; do not skip levels.
6. Prefer three to seven top-level branches unless the source requires otherwise.
7. Pass root, branches, leaves, cross-links, selected structure, and style preference to `processon-prompt`.

## Quality rules

- Apply MECE where it fits, but preserve source truth over forced symmetry.
- Keep siblings grammatically parallel and similar in detail.
- Move long explanation outside nodes; do not paste paragraphs into a branch.
- Use cross-links only when they materially improve understanding.
- For fishbone analysis, distinguish observed causes from hypotheses.
- For WBS, describe deliverables or outcomes rather than vague activities.
- For timelines, label dates, phases, and milestone outcomes consistently.

## Visual defaults and customization

Use balanced branch density, consistent depth, restrained colors by top-level branch, readable node spacing, and a clear center or root. Accept preferences for orientation, palette, density, audience, presentation tone, and whether icons should identify categories. Do not use decorative emoji or images unless they improve recognition.

## Accuracy, privacy, and boundaries

- Read supplied material before summarizing it; do not infer unavailable document contents.
- Do not invent conclusions, evidence, dates, owners, or priorities.
- Never include credentials, private local paths, or unrelated personal information.
- If the input is a process, interaction, data schema, or runtime architecture, route to `processon-diagram` instead.
- If the goal is a report-ready comparison or visual story rather than knowledge navigation, route to `processon-infographic`.

## Chinese starter examples

- “把这份方案整理成向右展开的逻辑图，保留原有章节并压缩末级内容。”
- “用鱼骨图分析线上模型准确率下降的可能原因，区分事实与待验证假设。”
- “把项目拆成可交付成果导向的 WBS 树形图。”

Return the hierarchy model to the router; do not call ProcessOn directly.
