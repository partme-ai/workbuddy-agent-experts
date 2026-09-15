# Evidence-Based Quality Rubric

Line counts, table counts, and diagram counts are diagnostics, not success criteria. Evaluate each document against the outcomes below.

| Dimension | Pass condition |
|---|---|
| Purpose | Readers know the decision, action, or shared understanding the document enables |
| Scope | In-scope, out-of-scope, version, module, and audience boundaries are explicit |
| Evidence | Claims identify source, date, confidence, or owner; assumptions are labeled |
| Decisions | Chosen options include rationale, alternatives, consequences, and owner |
| Consistency | Names, versions, dates, milestones, APIs, architecture, and priorities agree with upstream documents |
| Completeness | Required states, exceptions, permissions, risks, acceptance criteria, and rollback/operations are addressed |
| Applicability | Optional architecture and business sections are included only when justified |
| Actionability | Owners, next steps, verification commands, deliverables, and unresolved questions are visible |
| Safety | No real secrets, private paths, unsafe default passwords, or unverified production commands are presented as ready to run |
| Readability | Headings are unique and ordered; links resolve after generation; diagrams clarify rather than decorate |

## Evidence labels

- `已确认：来源` — supported by source code, contract, research, test, or approved decision.
- `推断` — plausible but not directly specified.
- `假设` — deliberately assumed for planning and awaiting validation.
- `待确认` — missing or conflicting information blocks confidence.

## Completion rule

A document is complete when it passes the relevant dimensions and has no unresolved high-impact `待确认` item. More lines, tables, or diagrams do not compensate for missing evidence or decisions.
