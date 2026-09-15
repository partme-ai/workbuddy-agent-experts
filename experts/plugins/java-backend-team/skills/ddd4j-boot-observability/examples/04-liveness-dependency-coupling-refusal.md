# Example 4 — Coupling liveness to dependencies (boundary case)

## Prompt

> Ops wants the DB health check added to liveness too, so pods get recycled when the DB connection breaks. Quick config change in the observability module — right?

## What the skill should do

1. Decline the change as framed: liveness answers "is this process broken"; folding a dependency check into it makes the database's state decide whether the process lives — a category error with a production blast radius.
2. Explain the failure mode concretely: DB blip → liveness fails on every pod → kubelet restarts the whole service simultaneously → thundering herd on a database that was already struggling.
3. State that readiness is the correct signal for "cannot serve traffic" and it already aggregates dependency checks; recycling pods never fixes a remote dependency.
4. If connection-pool recovery is the real concern, address it as pool-level recovery/validation config in the data layer — not by redefining the probe contract.
5. Route the web/probe contract details to `ddd4j-boot-web` if the HTTP probe semantics need changing, and record the decision.

## Expected output

```
Request: DB health folded into liveness.
Verdict: do not use liveness for dependency state. Liveness failing on
a healthy process turns a remote dependency's blip into a simultaneous
restart of every pod (herd effect on the recovering DB).

Correct signals:
  readiness  — aggregates DB/MQ/cache; pods stop receiving traffic
               while the dependency is down, and recover without restart
  pool-level — connection validation/recovery config handles stale
               connections without redefining the probe

Handoff: probe HTTP semantics → `ddd4j-boot-web`.
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-web

missing: the actual stale-connection symptom ops observed; how to
provide: the pool error logs, so the recovery fix targets the real cause.
```

## Failure the skill must avoid

Making the change because "pods come back healthy afterwards". They do — after every pod restarted at once, amplified the DB load, and turned a two-minute blip into a twenty-minute outage.
