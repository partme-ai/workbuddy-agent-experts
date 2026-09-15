# Example 4 — Events between services is not a database problem

## Prompt

> Our services need to react to each other's changes. We're already using ddd4j-cloud data with MySQL — can we just add change-capture tables and let services poll them?

## What the skill should do

1. Recognize the near-miss: inter-service reaction is messaging, not data access — do not stretch the data skill into a broker substitute.
2. Say plainly: polling tables across services couples schemas, bypasses tenant filtering expectations, and has no delivery semantics; this is a `ddd4j-cloud-stream` concern.
3. Route: use `ddd4j-cloud-stream` for publishing and consuming change events with binding/destination naming, ACK, and retry semantics.
4. Keep the boundary explicit: the data skill still owns the source-of-truth writes and transactions; the stream skill owns propagation of those changes.
5. If the ask was really about reading another service's data, route the contract question to the owning service's API instead of shared tables.

## Expected output

```
Verdict: do not implement cross-service reaction via shared/poll tables.

Boundary:
  - ddd4j-cloud-data    → writes, transactions, migrations (this service)
  - ddd4j-cloud-stream  → change events between services (bindings, ACK,
    retry, tenant headers)

Handoff: Install: `npx skills add full-stack-skills/ddd4j-skills --skill
ddd4j-cloud-stream` for the eventing design.

Optional: if consumers need request/response semantics instead, that is
ddd4j-cloud-feign.
```

## Failure the skill must avoid

Designing the polling scheme "since we already have the data layer". Cross-service polling has no ACK/retry story, silently breaks tenant isolation assumptions, and turns every schema change into a cross-team contract change.
