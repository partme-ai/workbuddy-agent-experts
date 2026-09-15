# Example 3 — Evidence request: prove the EventStore against a real database

## Prompt

> The EventStore tests pass, but they run against H2 in-memory. Ops won't sign off. What do we need to show them?

## What the skill should do

1. Classify the current evidence honestly: H2 proves logic shape, not production behavior — it is SOURCE/TEST-low, not behavior-proven.
2. Specify the missing tier: QuarkusTest plus Testcontainers against the real engine (Postgres/MySQL as deployed), exercising EventStore append, read, and replay.
3. Include the failure paths ops cares about: connection loss mid-append, rollback, startup failure with a dead database.
4. Handle Docker honestly: if Docker is unavailable in the environment, the Testcontainers suite is BLOCKED/SKIPPED — reported as a risk, never PASS.
5. Output an evidence-status block with what each tier proves.

## Expected output

```
EventStore evidence:

  - H2 in-memory suite: PASS — proves query/replay logic only (not lock, not
    dialect, not real TX isolation).
  - Testcontainers Postgres round-trip (append/read/replay): NOT RUN.
  - Connection-loss mid-append / rollback: NOT RUN.
  - Startup failure with dead DB: NOT RUN.

Verdict: ops sign-off requires the Testcontainers tier on the release SHA.
Docker unavailable in this env? The suite is BLOCKED — reported as risk, NOT PASS.
How to provide: run `data` module QuarkusTest with Testcontainers profiles on CI.
```

## Failure the skill must avoid

Declaring "tests pass, we're good" from the H2 suite. H2's transaction and locking behavior differs from the production engine — signing off on it is the "container as success" inversion: claiming real-backend proof without a real backend.
