# Example 1 — WebFlux service wiring

## Prompt

> We're building a reactive API on Boot 3 with ddd4j. Wire it through ddd4j-boot: one error shape for everything, request context available to handlers, and duplicate submits rejected by idempotency key.

## What the skill should do

1. Fix the maintenance line, then read the web AutoConfiguration and the `ddd4j-webflux` module on that line.
2. Confirm WebFlux is the single assembled stack and the MVC starter is absent — the two cannot both own request handling.
3. Assemble the unified error handling so domain and framework failures return the ddd4j error contract, covering the validation path too.
4. Bind the request `Context` (Subject, tenant) for reactive handlers and prove release on success, error, and async completion.
5. Enable idempotency from the line's Properties and run contract tests: normal, error, replay with the same key, and async paths.

## Expected output

```
Stack: WebFlux only (MVC starter excluded) — line 3.x.

Wiring:
  - unified error contract for domain, framework, AND validation failures
  - Context binding per the webflux module's registrar; release on all
    three exit paths verified
  - idempotency enabled via configuration prefix from this line's
    Properties; replay of same key + body → stored first response

Contract tests:
  normal request            PASS
  domain error → contract   PASS
  validation error → contract PASS (registered before the handler chain)
  replay (same key)         PASS
  async context release     PASS

Evidence: SOURCE + HTTP contract TEST RUN. CI: NOT RUN.
```

## Failure the skill must avoid

Reusing the MVC error handler setup for WebFlux because "it's the same Spring". The exception routing, context binding, and async completion all differ — validation errors then escape the unified shape on exactly the reactive paths.
