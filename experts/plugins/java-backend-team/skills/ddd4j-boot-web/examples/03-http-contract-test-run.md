# Example 3 — HTTP contract test run

## Prompt

> Before go-live we need evidence for the web layer: prove the error contract, idempotency replay, and readiness all behave — not just that the app boots.

## What the skill should do

1. Fix the line and read the assembled contract from source: error mapping, idempotency semantics, readiness aggregation.
2. Run the four contract test classes the workflow names: normal, error, replay, and async paths.
3. For the error class, cover domain failure, framework failure, and validation failure — each must return the unified shape.
4. For replay, send the same idempotency key with the same body twice and assert the stored first response is returned and the handler ran once.
5. For readiness, kill a dependency (or simulate its failure) and assert the endpoint flips — a constant READY is a failed test, not a pass.

## Expected output

```
HTTP contract evidence (line 3.x, WebFlux):

  normal   200 + payload per contract                     PASS
  error    domain → contract 400/409 as mapped            PASS
           framework → contract 500, no stack trace       PASS
           validation → contract 422, field list only     PASS
  replay   same key twice → handler invoked once,
           second call returns stored response            PASS
  async    context bound during handler, released after   PASS
  readiness with DB down: endpoint reports DOWN           PASS
           (a hardcoded READY here would be a FAIL)

Evidence: HTTP contract TEST RUN. CI: NOT RUN for this SHA.
```

## Failure the skill must avoid

Reporting go-live readiness from a smoke test that only exercises the normal path. Three of the five tested behaviors — validation mapping, replay, dependency-failure readiness — are invisible to a "home page returns 200" check.
