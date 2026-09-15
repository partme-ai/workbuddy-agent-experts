# Example 5 — Readiness says UP while the database is down

## Prompt

> The database died during the night, but Kubernetes never restarted our pods — the readiness endpoint stayed 200 the whole time. Morning triage found every request failing while the probe said healthy. How?

## What the skill should do

1. Treat "probe green while dependency dead" as the classic hardcoded or stubbed readiness defect — the endpoint answered a constant instead of aggregating real checks.
2. Read the assembled readiness contributor on the line and determine what it actually evaluates: a real aggregate of dependency health indicators, or a static value.
3. Check why the wiring looks plausible: the health indicator beans may exist while the readiness aggregate ignores them (name mismatch, group exclusion, or a user bean replacing the default).
4. Fix the readiness assembly to aggregate the real checks and test it by simulating a dependency failure — the endpoint must flip.
5. Add the regression: a contract test that kills the dependency (or stubs its failure) and asserts readiness goes down, so a constant READY can never pass CI again.

## Expected output

```
Incident: DB unreachable from 02:14; readiness returned 200 throughout.

Read from source: the readiness endpoint returns a static aggregate —
it never consults the DB health indicator (group exclusion in the
assembled config). Every smoke test passed because nothing was down
when they ran.

Fix:
  1. readiness aggregates the real dependency indicators
  2. regression test: stub DB failure → readiness reports DOWN
  3. verify recovery: check restored → readiness UP

Evidence: SOURCE (readiness assembly read) + failure-simulation TEST
planned as regression gate.
```

## Failure the skill must avoid

"Fixing" it by making the probe stricter in Kubernetes config. The endpoint still lies — the fix belongs in what readiness aggregates, and only a dependency-failure test can prove it.
