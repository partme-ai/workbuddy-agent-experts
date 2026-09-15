# Example 1 — Cluster-safe idempotency with CAS

## Prompt

> Our payment API runs on 3 pods behind a load balancer. Duplicate submits from double-clicks are charging customers twice. The current guard is a Caffeine map. Fix it for ddd4j 2.0.x.

## What the skill should do

1. Diagnose: Caffeine is single-JVM — each pod has its own map, so a duplicate landing on a different pod is never seen.
2. Redesign on the shared atomic contracts: `AtomicCache` / `CasCache` with `CASOperation` and `GetsResponse`, backed by Redis (Lettuce/Jedis or Redisson).
3. Include the tenant and business key in the cache key, without PII.
4. Specify the TTL: long enough to cover the retry window, with re-acquisition semantics after expiry defined.
5. Demand the contention test: two independent clients, same key, one winner; plus network-failure and re-acquisition cases.

## Expected output

```java
// one winner per business key, cluster-wide
GetsResponse<Boolean> prior = atomicCache.gets(idemKey);
if (prior.exists() && prior.getValue()) {
    throw new DuplicateSubmissionException(idemKey);
}
boolean acquired = atomicCache.cas(
    idemKey, expected -> !expected, false, ttl);
```

Plus the test matrix: two-client contention (one winner), re-acquisition after TTL, Redis unreachable (must fail closed, not "succeed"), and a no-duplicate-submission assertion against two pods. Evidence tier: SOURCE design; Testcontainers contention test NOT RUN.

## Failure the skill must avoid

"Fixing" it by shrinking the Caffeine TTL or syncing the map. Both keep the per-JVM view; only a shared atomic compare-and-set closes the cross-pod window.
