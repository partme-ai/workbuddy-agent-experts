# Example 5 — Diagnosing the empty-Registry NPE after a partial startup

## Prompt

> Since Friday's deploy, roughly one in ten service starts serves requests that fail with an NPE inside `Contexts.current()` — and the health check said READY. Rollbacks don't always help. It's random. What is happening?

## What the skill should do

1. Read the signature: intermittent NPE from a static facade + READY anyway = registration raced or partially failed while readiness ignored participants.
2. Trace the startup sequence: which provider registers the context/subject bindings, what does it depend on, and can that dependency fail or arrive late (async init, external service, migration lock)?
3. Check readiness wiring: was `READY` hardcoded or bean-presence-based rather than aggregated over registered ports — explaining why a half-registered runtime accepts traffic.
4. Check rollback: when the late dependency fails, are the already-registered providers closed and the process marked failed — or does the runtime limp up half-wired?
5. Prescribe fixes and the testkit regression: readiness aggregation, fail-fast registration errors, reverse-order rollback, and a scenario forcing the late dependency to fail.

## Expected output

```
Diagnosis: partial startup + non-aggregated readiness.

Sequence on bad starts:
  t1: providers #1–2 register (Registry partially populated)
  t2: provider #3 (SubjectProvider) fails — DB migration lock timeout
  t3: runtime does NOT roll back or fail readiness (READY hardcoded from
      bean presence) → serves traffic
  t4: requests touching Contexts.current() → NPE (~the fraction of traffic
      hitting subject-scoped paths; "random" = path-dependent)

Fixes:
  1. readiness aggregates registered ports incl. SubjectProvider
  2. registration failure → fail fast + reverse-order rollback of #1–2
  3. duplicate/missing entry detection stays enabled

Regression (runtime-testkit): force provider #3 failure → process not
ready, #1–2 closed, zero served requests. Status: NOT RUN.
```

## Failure the skill must avoid

Adding a null-check around `Contexts.current()` to "stop the NPE." That masks a half-registered runtime serving traffic — the defect is the missing readiness aggregation and rollback, not the null.
