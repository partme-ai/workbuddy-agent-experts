---
name: processon-infographic
description: Model report-ready ProcessOn infographics by matching comparison, cycle, matrix, progression, hierarchy, and radial relationships to an appropriate visual layout. Use for concise communication visuals, not technical notation or deep knowledge navigation.
---

# Infographic Modeling

Select layout from the information relationship, then build concise content and a coherent visual system for `processon-prompt`.

## Relationship-to-layout map

| Information relationship | Preferred layout |
|---|---|
| Two or more alternatives | comparison columns or split comparison |
| Repeating stages or feedback | cycle or ring |
| Two dimensions or four themes | matrix or quadrant |
| Ordered maturity or growth | staircase, S-curve, or rising path |
| Ranked levels or narrowing focus | pyramid or cone |
| One center with peer themes | radial or ray layout |
| Short ordered story | single row or single column |
| Equal categories or compact metrics | multi-row grid |

The documented ProcessOn family also includes multi-column, multi-row, circular, S-shaped, stepped, conical, matrix, ray, comparison, and cyclic structures. Use the simplest layout that communicates the relationship.

## Content model

1. Define one communication objective and one title.
2. Extract three to seven primary information units.
3. Give each unit a short heading and one concise fact, metric, or action.
4. Identify ordering, comparison axes, center relationship, or cycle direction.
5. Remove repeated prose and decorative filler.
6. Add a source or scope note when metrics could be misunderstood.
7. Pass content units, relationship, layout, audience, and style to `processon-prompt`.

## Visual system

- Use one dominant focal point and predictable scan order.
- Keep category colors consistent and contrast accessible.
- Prefer flat shapes, clear whitespace, short labels, and restrained icon use.
- Use numeric emphasis only for real metrics supplied by the user.
- Avoid gradients, 3D effects, excessive shadows, and unrelated stock imagery unless explicitly requested and readability remains intact.
- For executive material, reduce density; for operational material, preserve actionable detail.

## Accuracy and boundaries

- Do not invent percentages, rankings, research findings, or business outcomes.
- Do not force chronological content into a comparison or independent themes into a cycle.
- Ask one question only if the missing audience, dimensions, or ordering changes the layout.
- Never include credentials, private identifiers, or unrelated context in the prompt.
- Route processes and technical notation to `processon-diagram`; route deep hierarchical knowledge to `processon-mindmap`.

## Chinese starter examples

- “把 Agent 生产就绪度做成质量、安全、可靠性、运维四象限信息图。”
- “把产品从试点到规模化的五个阶段做成阶梯信息图。”
- “把三个技术方案按成本、性能、风险和维护性做成对比信息图。”

Return the content-layout model to the router; do not call ProcessOn directly.
