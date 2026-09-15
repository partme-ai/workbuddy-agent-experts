# Example 3 — Producing cross-runtime alignment evidence

## Prompt

> We maintain the ddd4j web adapters for webmvc, javalin, and vertx. A bug in vertx turned out to exist in all three but was only noticed on vertx. Give us the evidence process that would have caught this everywhere at once.

## What the skill should do

1. Name the mechanism: `web-testkit` endpoints and assertions are the shared contract — every adapter must pass the identical suite.
2. Define the suite coverage: response shape, each error status mapping, context propagation, authentication failure classes, idempotency replay, CORS behavior, readiness responses.
3. Require the suite runs per adapter per change — not "the contract was ported carefully."
4. Add the thread-reuse case to every run: a request ending on a worker thread must leave no context residue for the next.
5. Grade the evidence and make alignment a release gate rather than a best practice.

## Expected output

```
Alignment process:

Contract: web-testkit suite (same paths + payloads for every adapter)
  1. unified response shape
  2. error mapping: 400/401/403/404/409/415/422/429/500
  3. context headers propagate Request/Trace/Tenant/Subject
  4. auth failure classes → stable statuses
  5. idempotency replay → same-key second request handled per scope
  6. CORS allowlist behavior
  7. readiness vs liveness responses
  8. same-thread reuse after request end → zero residue

Gate: all three adapters (webmvc, javalin, vertx) green on the same suite
before any web-module release.

Incident mapping: the vertx context bug would have failed item 3 (or 8) on
all three adapters — surfacing on webmvc and javalin too.
Status of current adapters against the suite: NOT RUN — first execution is
the baseline.
```

## Failure the skill must avoid

Answering "add more unit tests to the vertx adapter." Per-adapter unit tests are exactly what allowed the drift — the missing piece is one shared suite that cannot pass on a diverged adapter.
