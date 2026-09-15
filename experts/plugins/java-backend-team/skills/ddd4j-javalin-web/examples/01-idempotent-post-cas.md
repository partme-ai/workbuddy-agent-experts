# Example 1 — Idempotent POST with shared CAS

## Prompt

> Our payments POST gets retried by the client on network timeouts, so we sometimes charge twice. Make the endpoint idempotent — we run three instances behind a load balancer.

## What the skill should do

1. Confirm the line (for example 7.1.x → Javalin 7.1/ddd4j 2/JDK 17/Maven 3) and read the web module's idempotency support and web-testkit replay paths.
2. Establish the client-supplied idempotency key contract (header, validation, error response when absent) via the HTTP contract before code.
3. Back the key check with the distributed cache's shared CAS — with three instances, a local map or Caffeine instance deduplicates only within one JVM.
4. Write the failing contract first: replaying the same key must return the original response (or the agreed replay status), and a second instance must observe the same rejection — then run the replay and cross-instance tests.

## Expected output

```java
app.beforeMatched("/api/payments", ctx -> requireIdempotencyKey(ctx));

// handler: acquire shared CAS on key → miss: process, store response
//          hit: return stored response (replay), never re-charge
```

Evidence block:

```
| Case                                   | Expected            | State |
|----------------------------------------|---------------------|-------|
| First request, key K                   | 201, charged once   | PASS  |
| Replay key K, same instance            | stored response     | PASS  |
| Replay key K, different instance       | stored response     | PASS  |
| Key K in-flight concurrent replay      | one process, one 201| PASS  |
```

## Failure the skill must avoid

Backing the idempotency check with a Caffeine cache because "it's fast" and passing the single-instance replay test. With three instances the same payment still charges twice — the shared CAS contract exists precisely for this deployment.
