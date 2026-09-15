# Example 2 — Cache key and TTL review (read-only)

## Prompt

> Review our cache layer before the security audit. Keys, TTLs, and what happens when Redis is down — I don't want surprises.

## What the skill should do

1. Stay read-only — findings, not rewrites.
2. Audit key structure: business domain + tenant + version + stable identifier present; PII (phone numbers, ID numbers, tokens) absent.
3. Audit TTL usage: units correct per implementation, zero/negative values handled, and expiry actually set (no immortal keys).
4. Audit lock usage: owner recorded, timeout set, release guaranteed on exception paths.
5. Audit failure behavior: Redis outage → explicit degradation, not silent business success.

## Expected output

| Finding | Location | Severity |
|---|---|---|
| Key `order:{orderId}` missing tenant segment | `OrderCacheKey.java:14` | high — cross-tenant read possible |
| Key contains raw phone number | `SmsCacheKey.java:22` | high — PII in observable keys; hash or internal ID required |
| `tryLock` without `finally` release | `StockLock.java:57` | high — lock survives the failed holder until TTL |
| Redis down → catch → return cached-default "OK" | `PaymentGuard.java:41` | critical — outage becomes invisible data risk |
| TTL units documented and tested for JetCache provider | — | OK |

States clearly what was not verified: no Redis instance was exercised, so all TTL behavior findings are SOURCE-only.

## Failure the skill must avoid

Green-lighting the layer because "caching works." The audit exists to surface the tenant-less key and the exception-path lock leak — both invisible in a happy-path smoke test and both audit findings.
