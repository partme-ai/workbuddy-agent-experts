# Example 1 — Redis provider for cross-instance idempotency

## Prompt

> We run 6 pods and need idempotency keys to hold across all of them. Wire the cache through ddd4j-boot so the domain's Cache SPI is satisfied, and make sure the atomicity claim is real.

## What the skill should do

1. Fix the maintenance line, then read the cache AutoConfiguration and Properties on that line.
2. Rule out local providers: Caffeine/Guava/Hutool are per-JVM, so cross-instance idempotency requires Redis, Redisson, or JetCache.
3. Assemble the chosen provider via the boot cache module so the domain's `Cache` SPI resolves to it; keep defaults user-overridable.
4. Confirm connections have owners with rollback and idempotent close, and the off switch skips assembly entirely.
5. Prove the atomic semantics against a real Redis: concurrent CAS on the same idempotency key must produce exactly one winner.

## Expected output

```
Selection: Redis (via Redisson client) — local providers cannot satisfy
cross-instance idempotency.

Wiring:
  - Cache SPI bound to the Redis-backed implementation (boot cache module)
  - configuration prefix per the line's Properties; TTL units confirmed
  - @ConditionalOnMissingBean guards verified; off switch tested (0 beans)
  - client shutdown path: idempotent close on context stop

Proof (real Redis, 32 threads, same key):
  CAS winner count = 1            PASS
  TTL expiry at configured bound  PASS

Evidence: SOURCE + behavior TEST RUN. CI: NOT RUN.
```

## Failure the skill must avoid

Assembling a local Caffeine cache because it is fastest and claiming idempotency works. Each pod would hold its own key space — duplicate processing across pods is the exact failure this selection rule prevents.
