# Example 5 — The pod that restarts on every DB blip

## Prompt

> Since last week Kubernetes restarts our 7.1.x pods whenever PostgreSQL hiccups for a few seconds. Restart loops during a DB incident are making things worse. What did we get backwards?

## What the skill should do

1. Diagnose the inversion: the health endpoints have their semantics swapped — liveness is checking the database (a dependency), so a downstream outage fails liveness and the platform kills healthy pods.
2. Trace the endpoint wiring on 7.1.x: find which handler serves liveness and which serves readiness, and confirm the DB check landed in the wrong one.
3. Specify the contract: liveness is process-only (the process can serve a response ⇒ alive); readiness aggregates real dependencies (DB, MQ, OIDC, Outbox) so the load balancer sheds traffic instead of the platform restarting pods.
4. Provide the failing tests first: DB-down must fail readiness but keep liveness passing; then re-run and report evidence.

## Expected output

```
Diagnosis: liveness and readiness are inverted.
  - /live (HealthConfig.java:29) calls db.ping()          ← dependency in liveness
  - /ready (HealthConfig.java:41) returns constant true   ← constant in readiness

Effect during DB incident: liveness fails → kubelet restarts pod →
restart loop while the DB is down; readiness never shed traffic.

Fix (contract-first):
  1. RED: DB participant down → /ready NOT READY, /live still 200.
  2. /live = process-only; /ready = aggregated required/optional participants
     (required down ⇒ NOT READY; optional down ⇒ explicit DEGRADED).
  3. GREEN: verify shed-traffic behavior, no restarts.

Evidence: SOURCE read; contract tests NOT RUN on this checkout.
```

## Failure the skill must avoid

"Fixing" the restart loop by making both endpoints always return 200. That trades a restart storm for traffic into a dead dependency; the real fix is the liveness/readiness split with aggregated readiness.
