---
name: processon-diagram
description: Model professional ProcessOn flowcharts, swimlanes, UML and sequence diagrams, architecture and ER diagrams, organization and equity charts, timelines, and business-analysis diagrams. Use after the ProcessOn router selects a professional diagram rather than a mind map or infographic.
---

# Professional Diagram Modeling

Turn user facts into a topology that `processon-prompt` can express precisely. Focus on relationships and runtime meaning, not decoration.

## Select the diagram family

| User intent | Family | Required model |
|---|---|---|
| Process, decisions, exceptions | Flowchart | start/end, actions, decisions, labeled outcomes |
| Cross-role process | Swimlane | lanes, owners, handoffs, decisions, exceptions |
| Ordered system interaction | Sequence diagram | participants, messages, returns, alternatives, failures |
| System composition or deployment | Architecture | boundaries, components, dependencies, protocols, data/control flows, trust zones |
| Data model | ER diagram | entities, key fields, PK/FK, cardinality, optionality |
| Software types and behavior | UML class/state/use-case/requirement | standard UML semantics for the requested view |
| Reporting hierarchy | Organization chart | roles, reporting lines, groups, vacant/shared roles |
| Ownership or control | Equity/relationship diagram | subjects, percentages or relation labels, direction |
| Milestones and evolution | Timeline | dates/phases, milestones, outcomes |
| Business analysis | SWOT, PEST, pyramid | named dimensions, concise evidence, priority |

Honor an explicit family unless it cannot represent the requested relationship. Explain any necessary mapping.

## Structure workflow

1. Extract facts without changing meaning.
2. Create a compact list of nodes or participants.
3. Define every meaningful relationship and its direction or label.
4. Separate the primary path from exceptions, optional flows, and annotations.
5. Choose orientation and grouping from the topology.
6. Pass the structure to `processon-prompt`.

## Family-specific rules

- **Flowchart:** use one start and at least one explicit end; decisions are questions with labeled outcomes; do not hide error paths in prose.
- **Swimlane:** each action belongs to exactly one accountable lane; show handoffs at lane boundaries; avoid a lane per individual unless required.
- **Sequence:** time runs top to bottom; distinguish synchronous calls, asynchronous messages, replies, loops, and alternatives.
- **Architecture:** default to an architecture block diagram with large labeled components inside explicit layers or boundaries. Show runtime or deployment boundaries, dependencies, protocols, trust zones, data/control direction, resilience, and observability where relevant. Do not use UML class tables, attribute rows, method compartments, or placeholder field types unless the user explicitly requests a class diagram. Never substitute a directory tree.
- **ER:** include only decision-relevant fields; mark primary and foreign keys; label one-to-one, one-to-many, or many-to-many cardinality and optionality.
- **UML:** choose one view that answers the question; do not mix class, state, use-case, and sequence notation on one canvas.
- **Organization/equity:** separate reporting, ownership, governance, and collaboration relations; label ambiguous edges.
- **Timeline:** use a consistent time scale or explicitly label non-linear phases.
- **SWOT/PEST:** facts stay in the correct dimension and are phrased as concise evidence, not slogans.

## Visual constraints

Use a clear reading direction, restrained palette, consistent shapes for equivalent semantics, adequate contrast, short labels, balanced whitespace, and minimal connector crossings. Use semantic colors sparingly for success, warning, risk, or ownership.

## Accuracy, privacy, and boundaries

- Do not invent components, protocols, owners, cardinalities, dates, percentages, or metrics.
- Ask one question only when a missing answer changes topology; otherwise state a conservative assumption.
- Never include credentials, local paths, private identifiers, or unrelated context in the generation prompt.
- If source code or documents are required, inspect them before modeling; a filename list is not architecture evidence.
- If the current MCP cannot edit an existing file, offer a new diagram based on supplied content and disclose the limitation.

## Chinese starter examples

- “画一个包含登录、风控、支付失败和补偿路径的标准流程图。”
- “把产品、算法、后端、测试、运维的 AI 上线流程画成泳道图。”
- “根据当前源码画运行时架构图，标出协议、信任边界、数据流和故障恢复。”

Return the structure model to the router; do not call ProcessOn directly.
