# Example 2 — Read-only cache wiring review

## Prompt

> Review our cache wiring read-only before we scale to three replicas. Line 3.3.x. I want to know what silently breaks.

## What the skill should do

1. Stay read-only and fix the line/SHA (3.3.x → Quarkus Platform 3.37.4 / ddd4j 2.0.x / JDK 17 / Maven 3).
2. Identify every cache provider bean and its CDI scope — flag `@Dependent` providers that fork per injection point.
3. Classify each cache use: data caching (TTL) versus idempotency (CAS) — flag idempotency keys sharing an evicting data cache.
4. Check connection lifecycle: startup/shutdown observer ownership, idempotent close.
5. Check native registrations for cached payload types.

## Expected output

| Check | Finding | Verdict |
|---|---|---|
| Provider scope | `@Dependent` on `CacheProvider` — one instance per injection point | **DEFECT** |
| Data cache | Quarkus Cache, TTL 5m, fine for data | OK |
| Idempotency | keys stored in the same 5m cache — evicted early | **GAP** |
| Lifecycle | connections owned by observer; close idempotent | OK |
| Native | payload type registrations present | OK |

Scaling impact: at three replicas the `@Dependent` scope multiplies the forked caches per instance.
Evidence: SOURCE read. QuarkusTest cache suites NOT RUN on this SHA.

## Failure the skill must avoid

Approving the setup because "caching works in staging". Staging runs one replica with one injection path — the scope fork and the TTL-evicted idempotency keys only appear under real topology.
