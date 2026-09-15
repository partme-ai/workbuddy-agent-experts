# Example 1 — Cross-line hardening execution under an approved plan

## Prompt

> The Phase D plan was approved last week: harden readiness aggregation and CORS across all three Javalin branches, TDD style. Execute it — branch 6.7.x first.

## What the skill should do

1. Establish truth before touching files: repo root, branch/worktree state, dirty files, current plan status, and each line's actual contract re-derived from POMs and wrappers (not the historical matrix).
2. Audit the plan instead of trusting checkboxes — classify each Phase D task as DONE, STALE, OPEN, or BLOCKED, linking every completion to source plus executed verification.
3. Convert the risks into failing contracts per line: readiness constant while a required participant is down must flip to NOT READY; a disallowed CORS origin must be rejected with credentials/method/header policy enforced.
4. Implement on the authoritative line first (6.7.x, JDK 17/Maven 3), then adapt deliberately to 7.1.x and 7.2.x — preserving each line's syntax, POM model, and Javalin 6/7 API differences.

## Expected output

```
Phase: execute (plan approved) | Fact source: docs/superpowers/plans/phase-d.md
Files will change: yes (3 branches)

Per-line progress:
  feature/6.7.x: readiness contract RED→GREEN (4 tests), CORS contract RED→GREEN (3 tests),
                 affected module regression 41/41, clean reactor PASS (JDK 17/Maven 3)
  feature/7.1.x: same contracts adapted (Javalin 7.1 API), 7/7 green
  feature/7.2.x: adapted (JDK 21/Maven 4, Javalin 7.2), 7/7 green

Evidence tiers: focused + regression + per-line clean reactor PASS.
Container/CI tiers: NOT RUN — next gate before release.
```

## Failure the skill must avoid

Marking Phase D complete after porting the 6.7.x implementation to the other two branches and running only the new tests. Cross-line porting without per-line regression plus reactor evidence is exactly the collapse of delivery states this skill exists to prevent.
