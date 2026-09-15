# Example 2 — Read-only production-readiness review

## Prompt

> Review mode: our three Javalin branches claim "production ready". Audit the actual gaps and tell me whether the plan checkboxes reflect reality. Change nothing.

## What the skill should do

1. Stay read-only — review mode, no edits, no pushes.
2. Re-derive each branch's contract from POMs, wrappers, CI workflows, and tests; treat the historical branch matrix as a hypothesis only.
3. For each plan task, classify DONE/STALE/OPEN/BLOCKED by tracing actual behavior: readiness aggregation, `JavalinLifecycleParticipant` ordering, idempotency backing, CORS policy, shutdown hooks.
4. Report the gap list per branch with the evidence tier each gap needs, and call out any checkbox whose completion has no linked verification.

## Expected output

```
Readiness review (read-only):

| Concern                  | 6.7.x        | 7.1.x        | 7.2.x        |
|--------------------------|--------------|--------------|--------------|
| Readiness aggregates deps| OPEN (constant READY) | DONE (verified) | DONE (verified) |
| Shared-CAS idempotency   | DONE         | DONE         | OPEN (Caffeine in prod profile) |
| Explicit CORS            | DONE         | DONE         | DONE         |
| Hook accumulation        | STALE (checkbox done, no test) | DONE | DONE |

Plan truth: 2 of 14 "completed" tasks lack linked verification (STALE).
Gates to production acceptance: container tier NOT RUN on any branch.
```

## Failure the skill must avoid

Accepting "production ready" because the plan shows all checkboxes ticked. The review found a constant-READY branch and a stale checkbox — exactly the checkbox-trust anti-pattern this skill's review mode exists to catch.
