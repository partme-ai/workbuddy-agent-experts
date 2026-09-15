# Example 4 — Restructuring the core domain types

## Prompt

> While you're reviewing the module layout, also split `AggregateRoot` into two interfaces and move `Repository` into the data module. That'll clean things up nicely.

## What the skill should do

1. Decline the core restructure: `AggregateRoot` and `Repository` are `ddd4j-core` contracts, and this skill governs Javalin adapter layering, not the framework-agnostic SPI.
2. Explain the boundary — moving core types into a Javalin adapter module inverts the dependency direction for every runtime, not just Javalin.
3. Hand off the core design question to `ddd4j-core`, and offer to execute the Javalin-side consequences (module updates, tests) once the core contract change is decided.
4. Record the boundary in the review report so the board sees it as a routing decision, not an oversight.

## Expected output

```
Out of scope for this review (routing, not refusal of the goal):
  - Splitting AggregateRoot: core contract change → ddd4j-core skill.
    Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core
  - Moving Repository into the data module: violates adapter → core direction
    for all runtimes; same core boundary.

This skill will take the Javalin-side follow-up after the core decision:
update module dependencies, adapt runtime wiring, run per-line contract tests.
```

## Failure the skill must avoid

Cheerfully moving `Repository` into the Javalin data module because it "cleans up the layout". That is a cross-runtime contract change disguised as a packaging tweak, and it is the boundary this skill must not cross.
