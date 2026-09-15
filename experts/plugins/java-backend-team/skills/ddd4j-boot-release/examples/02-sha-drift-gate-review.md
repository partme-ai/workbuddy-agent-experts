# Example 2 — Release gate review (read-only)

## Prompt

> Release is tomorrow. Read-only check of our release readiness: are the evidence records for each line actually valid, or is anything inflated?

## What the skill should do

1. Stay read-only; audit the evidence, do not run the release.
2. Fix the line set, then compare each line's recorded CI SHA against the final release SHA.
3. Classify every evidence item honestly: a CI run for an older SHA does not gate the final code; a non-started job is BLOCKED, not pending-pass.
4. Check the security stage records — exemptions must exist as SKIPPED with an owner and reason, not as passes.
5. Check that every PUBLISHED claim is backed by a deploy record and every CONSUMED claim by a clean-cache run.

## Expected output

| Line | CI SHA matches final | Deploy record | Clean-cache consume | Verdict |
|---|---|---|---|---|
| 2.7.x | yes | yes | yes | CONSUMED — valid |
| 3.5.x | no (CI ran SHA^) | yes | yes | CI INVALID — re-run required |
| 4.0.x | yes | no | "tested locally" | PUBLISHED UNPROVEN |
| 3.0.x | yes | yes | job never started | CONSUMED INVALID — BLOCKED |

Release verdict: NOT READY. Two lines need re-runs, one needs a deploy,
one is BLOCKED. Evidence stays graded per line — no averaging.

## Failure the skill must avoid

Accepting "CI is green" from the dashboard. One line's green run belongs to the parent commit and another never consumed anything — reading the SHA and the clean-cache record is the entire job of this audit.
