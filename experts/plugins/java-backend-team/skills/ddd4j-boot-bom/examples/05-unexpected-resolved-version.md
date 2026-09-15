# Example 5 — Dependency resolved to the wrong version

## Prompt

> We upgraded the parent to the new 3.x patch and suddenly one of our libraries comes in at an older version than before. Nothing in our module pins it. Where did that come from?

## What the skill should do

1. Treat "version changed without any local pin" as a BOM-layer question, not an application-code question.
2. Fix the line and diff the effective POM before and after the parent bump (`mvn help:effective-pom`).
3. Identify which managed entry moved: the Spring Boot BOM alignment, the ddd4j BOM, or ddd4j-dependencies.
4. Check import order — a reordering or a new import in the parent can silently change which BOM wins an overlapping coordinate.
5. Prescribe the compliant fix (adjust ownership at the governing POM) rather than re-pinning in the module.

## Expected output

```
Diagnosis:
  before parent bump: lib-X resolves to 4.1.2 (from Spring Boot BOM alignment)
  after parent bump:  lib-X resolves to 4.0.9 (new ddd4j BOM import now
                      wins the overlapping coordinate)

Root cause: the parent's import order gives the ddd4j BOM precedence for
this coordinate on the new line. No module pin is involved.

Compliant fix: adjust the coordinate in the governing BOM for this line
(or reorder imports deliberately), then re-verify the effective POM.
Do not pin the version in the consumer module.

Evidence: SOURCE + effective-POM diff. Downstream tests NOT RUN.
```

## Failure the skill must avoid

"Fixing" it with a `<version>` in the application module. That restores the expected build locally while leaving the ownership conflict in place — the same surprise then hits every other consumer of the BOM.
