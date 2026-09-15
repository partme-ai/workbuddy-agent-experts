# Example 1 — Redis-backed Cache SPI with shared CAS

## Prompt

> Our service runs two replicas and payment submissions must be replay-safe. We're on ddd4j-quarkus 4.0.x. Which cache setup do we need?

## What the skill should do

1. Fix the line (4.0.x → Quarkus Platform 3.38.2 / ddd4j 3.0.x / JDK 21 / Maven 4) and read the cache adapter in that checkout.
2. Select the provider against the consistency target: two replicas with replay protection require a shared store — Redis behind the ddd4j `Cache` SPI, not local Quarkus Cache.
3. Register the provider as a singleton-scoped CDI bean with configuration mappings, so one cache instance serves the application.
4. Give idempotency keys their own TTL budget, separate from short-TTL data caching.
5. Plan the tests: TTL, invalidate, and a real CAS contention test across two simulated instances.

## Expected output

```
Provider: Redis-backed ddd4j Cache SPI (shared across replicas).
Registration: @Singleton CDI provider; connection owned by startup/shutdown
              observers; idempotent close.
Idempotency: CAS on key `idem:<operation>:<key>`; TTL 24h (own namespace, not the
             data-cache TTL of 5m).

Tests (QuarkusTest):
  - TTL eviction after the data-cache window.
  - invalidate removes only its namespace.
  - CAS contention: two threads, same key → one wins, one gets the existing result.
  - Two-replica replay: same key on "replica B" returns replica A's result.
```

## Failure the skill must avoid

Keeping local Quarkus Cache "since it's already on the classpath" and calling it replay-safe. A local cache is per-replica — the second replica has never seen the key and processes the replay as new.
