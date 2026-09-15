# Example 5 — Green H2 suite, broken MySQL behavior

## Prompt

> All our data-layer tests pass in CI, but in staging the tenant filter doesn't apply and one migration won't run on MySQL. Tests were green — what's going on?

## What the skill should do

1. Name the likely root cause up front: the suite ran against an in-memory database, but the line's compatibility pairing is WebMVC/MySQL — H2 green is not MySQL evidence.
2. Check the two classic divergences: SQL syntax/dialect differences that break the migration on MySQL, and the tenant filter depending on MySQL-specific behavior the stub database did not exercise.
3. Re-run the failing migration and the tenant isolation tests against real MySQL, grading the evidence honestly.
4. Fix the migration for the real dialect and verify filtering activates only after the tenant column exists.
5. Mark the CI suite's coverage gap: either add container-based MySQL runs where Docker exists, or record the tier as NOT VERIFIED per run.

## Expected output

```
Root causes:
  1. Migration V11 uses H2-only syntax — fails on MySQL 8.
  2. Tenant filter verified only on the stub DB; real-MySQL filter test
     never ran, so the missing-filter staging symptom was invisible in CI.

Fixes: rewrite V11 for the MySQL dialect; add container-based MySQL runs
to CI (Docker present) or mark the tier NOT VERIFIED per run.

Evidence: TEST (real MySQL) after fix — PASS; previous CI tier downgraded
to "in-memory only" in the report.
```

## Failure the skill must avoid

Patching the migration until H2 *and* MySQL both pass and calling it done. The systemic failure is the evidence tier: a suite that never touches MySQL cannot certify the WebMVC/MySQL pairing, and the report must say so.
