# Example 2 — Read-only review: Caffeine in the production profile

## Prompt

> We scaled from one replica to three last month and I want a read-only audit of our cache setup on 6.7.x before the next review. Something feels off with idempotency.

## What the skill should do

1. Stay read-only; produce findings with file/line evidence.
2. Identify which cache backs idempotency per profile: if the production profile resolves to Caffeine (default or by omission), scaling to three replicas silently broke cross-instance dedup.
3. Check whether the Caffeine usage is at least explicit (named dev/single-instance fallback) versus accidental default wiring.
4. Check lifecycle: the cache provider's owner, shutdown order, and whether CAS unavailability has a defined path in the distributed option.

## Expected output

| Check | Finding | Verdict |
|---|---|---|
| Idempotency backing (prod profile) | resolves to Caffeine via default (`CacheConfig.java:39`) | VIOLATION — multi-instance needs shared CAS |
| Caffeine explicitly documented as fallback | not documented anywhere | VIOLATION — silent default |
| Lifecycle owner | registered participant, close idempotent | OK |
| CAS failure path | distributed provider present but unconfigured | GAP — fail-closed path undefined |

Scaled-to-three impact: each replica dedups only its own keys; the same write key processed on two replicas creates duplicates.

Plus: what was not verified (no contention test executed in this review).

## Failure the skill must avoid

Concluding "caching is fine, we use Caffeine with TTL configured". TTL is irrelevant to the defect — the backing store is per-JVM, and the audit must connect the scaling event to the broken cross-instance guarantee.
