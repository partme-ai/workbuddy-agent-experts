# Example 1 — Shared-CAS idempotency for a multi-instance deployment

## Prompt

> Our order service runs on four replicas and we need write idempotency that actually works across them. The client sends an Idempotency-Key. What backend and config do we use on 7.2.x?

## What the skill should do

1. Confirm the line (7.2.x → Javalin 7.2/ddd4j 3/JDK 21/Maven 4) and read the cache module's distributed provider and CAS contracts.
2. Select the distributed Cache with shared CAS as the idempotency backing — state plainly that Caffeine is excluded for this deployment except as a documented dev fallback.
3. Register the provider as a lifecycle participant with an owner, idempotent close, and readiness contribution where required.
4. Provide the failing contracts first: the same key from two different replicas must produce one effect, and CAS unavailability must fail closed rather than process.

## Expected output

```java
// production profile: distributed Cache with shared CAS
runtime.register(new DistributedCacheParticipant(casConfig)); // owner + idempotent close

// idempotency acquire: CAS on key; miss → process; hit → replay stored response
// CAS unavailable → fail closed (503), never fall through to processing
```

Evidence block:

```
| Case                                  | Expected            | State |
|---------------------------------------|---------------------|-------|
| Same key, replicas A and B concurrent | one effect          | PASS  |
| CAS down during acquire               | explicit 503, no effect | PASS |
| Lock TTL expires mid-operation        | explicit re-acquire path | PASS |
| Dev profile (Caffeine documented)     | single-instance only | noted in config |
```

## Failure the skill must avoid

Shipping Caffeine "for now" in the four-replica production profile without flagging it. Four replicas with four local caches means four chances to double-process the same key — the deployment decision this provider selection exists to make.
