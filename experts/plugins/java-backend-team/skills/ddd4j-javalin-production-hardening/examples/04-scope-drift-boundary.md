# Example 4 — Scope drift toward the upstream core

## Prompt

> While hardening our Javalin branches, we found the readiness SPI in ddd4j-core is awkward. Just refactor the core interfaces while you're in there — it'll make the Javalin fix cleaner.

## What the skill should do

1. Keep the request Javalin-only: an upstream `ddd4j-core` refactor is out of scope unless current Javalin evidence proves it is a dependency blocker — awkward-but-workable does not meet that bar.
2. State the blast radius: core SPI changes fan out to Boot, Quarkus, and Cloud adapters, all outside this delivery's authorized scope.
3. Record the dependency blocker formally instead (scope note in the plan: "core readiness SPI ergonomics — deferred"), and implement the Javalin hardening within the existing contract.
4. Name the escalation condition under which the scope expansion becomes legitimate: current evidence that the Javalin fix cannot land without the core change, plus explicit user authorization for the expanded scope.

## Expected output

```
Scope decision: core refactor DECLINED for this delivery.

Reason: no current Javalin evidence shows a blocker — the readiness hardening
lands against the existing core SPI on all three lines. A core interface
refactor would fan out to Boot/Quarkus/Cloud with no authorization.

Recorded instead:
  - Plan note (non-goal): "core readiness SPI ergonomics — deferred, tracked
    separately via ddd4j-core"
  - Javalin work proceeds: readiness aggregation + CORS contracts, 3 lines.

Escalation condition: current evidence that the Javalin fix cannot land without
the core change AND explicit user authorization for expanded scope.
```

## Failure the skill must avoid

Refactoring the core interfaces "since we're in the area". The Javalin branches get blocked on an unscoped, unauthorized multi-runtime change — the scope-drift anti-pattern this skill's decision rules exist to stop.
