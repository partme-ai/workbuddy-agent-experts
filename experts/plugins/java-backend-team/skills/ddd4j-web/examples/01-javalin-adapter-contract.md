# Example 1 — Implementing the contract in the Javalin adapter

## Prompt

> We're adding a Javalin edge service next to our Spring MVC monolith and both must speak the same ddd4j HTTP contract. What does implementing the contract on the Javalin side involve?

## What the skill should do

1. Read the `javalin` adapter's actual API and tests on the target branch — the contract is shared with `webmvc`, the idioms are not.
2. Define expected behavior via `web-testkit` paths and payloads first: unified response shape, error statuses, context headers.
3. Implement the pieces: context binding (Request/Trace/Tenant/Subject) at entry, authentication checks, exception translation to the stable statuses, cleanup on all exit paths.
4. Configure production controls: CORS allowlist, idempotency scope, request-size and async-timeout limits, readiness aggregating real dependencies.
5. Run the testkit suite on both runtimes and compare — alignment is the evidence.

## Expected output

```
Javalin adapter checklist (contract parity with webmvc):
  - before-handler: bind Request/Trace/Tenant/Subject
  - exception mapper: 400/401/403/404/409/415/422/429/500 → unified payload
    (cause preserved internally, no stack trace exposed)
  - after-handler + error path: context restore (success + exception + async)
  - CORS: explicit origin allowlist, credentials true only for those origins
  - readiness: aggregates DB + MQ probes; liveness process-only

web-testkit run: webmvc PASS (existing), javalin pending — alignment run is
the gate. Status: NOT RUN.
```

## Failure the skill must avoid

Porting the contract "from memory" of the Spring implementation without the testkit comparison. Each adapter drifts in its own direction — the shared behavior claim is only provable by running the same testkit suite on both.
