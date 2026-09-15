# Example 5 — The hardcoded READY

## Prompt

> Our readiness endpoint always returns ready almost instantly after boot, even when PostgreSQL is down. Load balancers keep sending traffic into a dead service. Why is it lying?

## What the skill should do

1. Diagnose the anti-pattern: readiness is hardcoded (a constant or a "port open" check) instead of aggregating real dependency state from the lifecycle participants.
2. Trace where readiness is computed in `Ddd4jJavalinRuntime` and enumerate which `JavalinLifecycleParticipant`s contribute state (DB, MQ, OIDC, Outbox) and which are ignored.
3. Specify the contract-first fix: a failing test where the required DB participant reports down and readiness must return not-ready; optional participants degrade the status explicitly but never report plain READY when required ones are down.
4. Keep liveness untouched and process-only — the fix must not make Kubernetes restart the pod on DB outage.

## Expected output

```
Diagnosis: readiness returns a constant after initialization
(ReadinessEndpoint.java line NN: `return READY`). No participant state consulted.

Fix contract (TDD):
  1. RED: required DB participant down → readiness = NOT READY (currently READY)
  2. RED: optional MQ participant down → readiness = DEGRADED (explicit, not READY)
  3. GREEN: all required up → READY
  4. Liveness unchanged: process-only, no dependency checks

Evidence: SOURCE read. Contract tests NOT RUN on this checkout.
```

## Failure the skill must avoid

"Fixing" it by pointing liveness at the database so Kubernetes restarts the pod on every DB blip. Readiness aggregates dependencies; liveness stays process-only — and the endpoint must stop returning constants.
