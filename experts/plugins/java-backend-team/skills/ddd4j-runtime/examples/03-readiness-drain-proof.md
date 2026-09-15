# Example 3 — Proving readiness, drain, and close with testkit

## Prompt

> We need sign-off that our Quarkus runtime wiring handles deploys cleanly: rolling restarts, in-flight requests during shutdown, and no half-registered state. What evidence do you need and how do we produce it?

## What the skill should do

1. Define the three claims precisely: readiness reflects real participants; in-flight work drains before close; close is idempotent and rolls back partial startups in reverse order.
2. Map each claim to a runtime-testkit scenario plus the Quarkus-native mechanism (CDI/Arc producers, observers, request scope).
3. Include the partial-startup scenario: force a late provider to fail and assert already-created resources (pools, buses) were closed in reverse order.
4. Include the duplicate-registration check: start with a doubled binding and assert fail-fast, not silent override.
5. Grade each run and record what remains unverified.

## Expected output

```
Claim → evidence mapping:

1. readiness aggregates: testkit readiness scenario with one dependency
   marked down → readiness must flip false (not hardcoded)
2. drain before close: in-flight request during SIGTERM → completes or
   fails cleanly AFTER close begins; no work abandoned mid-flight
3. idempotent close + reverse rollback: force provider #3 of 4 to fail →
   providers #1–2 closed in reverse; second close() call is a no-op
4. duplicate registration: doubled CommandBus executor binding → fail fast
   at startup

Run status: 1–2 NOT RUN, 3 NOT RUN, 4 NOT RUN — this plan is the gate.
Evidence grade after execution: TEST (testkit) per scenario.
```

## Failure the skill must avoid

Accepting "the app restarts fine in dev" as the sign-off. Rolling-restart behavior is exactly the sum of the four scenarios above — dev's single clean restart exercises none of the failure paths.
