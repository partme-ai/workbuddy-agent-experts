# Example 5 — Responses intermittently show another tenant's request id

## Prompt

> Every so often our API responses include a request-id header from a different request. It never happens locally. What is going on in our Quarkus web layer?

## What the skill should do

1. Pattern-match the symptom: cross-request values appearing intermittently in a pooled-thread runtime is a Context leak, not a header bug.
2. Trace the Context bind site (the REST filter) and its release; check the three exit paths — success, exception, and async completion.
3. Expect the defect: the filter binds the request id and tenant but releases only when the endpoint returns normally; an exception or async path skips the release.
4. Explain the rate: only error-path or async-path collisions leak, so single-request local testing never reproduces it.
5. Prescribe the fix and its test: release in a path that covers all three exits, plus a QuarkusTest that throws mid-request and asserts the next request on the same worker gets a fresh Context.

## Expected output

```
Bind: RequestContextFilter.bind(requestId, tenant) at request start.
Release: filter releases after chain.doFilter returns normally  ← exception and
async-completion paths skip release.

Leak scenario: request A throws → filter aborts before release → worker returns
to the pool with A's Context → request B's response decorated with A's request-id.

Fix: release in a finally-style path covering success, exception, and async
completion. Test: QuarkusTest asserting a fresh Context after a mid-request
exception on a reused worker thread.
Evidence: SOURCE read. Repro test NOT RUN — remaining gap.
```

## Failure the skill must avoid

Answering "add a filter that clears the header after each request" — another success-path-only patch. The leak lives on the exception/async paths, so the fix and the test must target those exits.
