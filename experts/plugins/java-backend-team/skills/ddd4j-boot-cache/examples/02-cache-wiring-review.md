# Example 2 — Cache wiring review (read-only)

## Prompt

> We had a stale-data incident last week. Read-only audit of our boot cache setup please — provider choice, TTLs, overrides, and anything that could bite us again.

## What the skill should do

1. Stay read-only; findings with severity, not patches.
2. Fix the line, then read the cache AutoConfiguration, Properties, and every cache-related bean the application declares.
3. Check the provider actually matches the consistency target for each cached concern (session-like data vs reference data).
4. Check TTL units and values against the line's Properties semantics, and flag any user bean that replaced a default.
5. Check the off switch scope, connection lifecycle, and whether any CAS/idempotency behavior has real-backend evidence.

## Expected output

| Check | Finding | Severity |
|---|---|---|
| Provider match | idempotency keys cached in local Caffeine (per-JVM) | Critical |
| TTL units | `ttl: 30` documented as seconds; line's Properties read milliseconds → 30s intended, 30ms actual | High |
| Override | user `CacheManager` bean replaces default; invalidation behavior untested | High |
| Off switch | `cache.enabled=false` leaves the health indicator assembled | Medium |
| CAS evidence | no test against a real backend; single-node fake only | Unverified |

Evidence: SOURCE read on line <L>. No behavior tests executed — read-only review.

## Failure the skill must avoid

Reporting "cache is configured correctly" because beans exist. The stale-data incident was caused by a per-JVM provider holding idempotency keys — a finding only visible when provider choice is compared against the consistency requirement.
