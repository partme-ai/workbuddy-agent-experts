# Example 3 — Verifying remote consumability of a chosen line

## Prompt

> We picked ddd4j-javalin 7.2.x for the new edge service. Before the team scaffolds, confirm the artifacts actually resolve — and don't just tell me the branch exists.

## What the skill should do

1. Restate what "confirm" means: not branch existence, but remote resolution of parent, BOM, and at least one representative JAR at the exact revision.
2. Verify the toolchain implication first: Javalin 7.2.x is the Maven 4 / POM 4.1 line — the team needs Maven 4 installed, or the scaffold fails before resolution matters.
3. Run the verification: private-repository metadata query for the revision, then a clean-cache `dependency:go-offline` / `compile` with `-U`.
4. Grade the result: PUBLISHED (metadata seen) vs CONSUMED (clean-cache resolve succeeded) — different claims.
5. Report unverified rows rather than assuming them.

## Expected output

```
Target: ddd4j-javalin 7.2.x (Javalin 7.2.3, ddd4j 3.0.x, JDK 21,
Maven 4 / POM 4.1)

Toolchain gate: Maven 4 required — flag to the team before scaffolding.

Remote check:
  - metadata for parent + BOM + javalin-web at 7.2.x revision: FOUND
    → PUBLISHED
  - clean-cache resolve (-U, empty local repo): SUCCESS
    → CONSUMED

Verdict: combination consumable end to end. Evidence: SOURCE + PUBLISHED +
CONSUMED. CI build of a scaffolded project NOT RUN — remains optional
follow-up.
```

## Failure the skill must avoid

Answering "yes, 7.2.x exists on the remote" from a branch listing and skipping the clean-cache gate. The two classic failures — a developer's warm cache masking a partial upload, and a Maven 3 toolchain choking on POM 4.1 — both survive that shortcut.
