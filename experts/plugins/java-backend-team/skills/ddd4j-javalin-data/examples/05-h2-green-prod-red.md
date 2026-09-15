# Example 5 — Green on H2, red on PostgreSQL

## Prompt

> Our data tests all pass in CI, but staging crashes on the first order insert with a dialect error, and under two parallel writes we got a deadlock PostgreSQL never showed us. Why did CI not catch this?

## What the skill should do

1. Diagnose the false green: the suite runs against an in-memory H2 substitute instead of real PostgreSQL, so dialects, locking, and constraint behavior differ exactly where the crash happened.
2. Check the suite's container usage on the current line — Testcontainers with PostgreSQL should back the round-trip tests, and if Docker is unavailable the result must be `BLOCKED`, not a silent H2 fallback marked PASS.
3. Translate the staging errors into contracts the suite must assert: the exact dialect-dependent statement, and the concurrent-write conflict path (expected exception, retry semantics).
4. Re-run the suite with real containers and report per-case evidence honestly.

## Expected output

```
Diagnosis: CI green ≠ PostgreSQL-verified.
  - Suite config (6.7.x): DataSource points at H2 mem when Docker is absent
    (TestDataConfig.java line NN) and marks the run PASS.  ← false green
  - Staging dialect error: H2 accepts the generated SQL, PostgreSQL does not
    (sequence/identity handling in OrderEntity mapping).
  - Deadlock: H2's locking never exercises the two-row update order that
    deadlocks on PostgreSQL.

Fix (contract-first):
  1. RED: run the insert suite on Testcontainers PostgreSQL — reproduce dialect error.
  2. Fix the mapping; assert conflict path with two parallel writers.
  3. Docker unavailable → BLOCKED, never an H2 fallback counted as PASS.

Evidence: SOURCE read. Container run NOT EXECUTED on this checkout.
```

## Failure the skill must avoid

Concluding "CI passed, so staging must be misconfigured". The suite's green was purchased with an in-memory substitute — the exact evidence conflation (skipped containers reported as behavior PASS) this skill exists to prevent.
