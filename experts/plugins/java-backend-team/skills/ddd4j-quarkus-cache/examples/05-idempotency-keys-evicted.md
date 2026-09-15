# Example 5 — Idempotency keys disappear after five minutes

## Prompt

> Weird bug: client retries always work in testing, but in production a retry after a network blip sometimes processes the payment twice. The blips are a few minutes apart. What's happening?

## What the skill should do

1. Connect the timing to eviction: idempotency keys stored in a cache whose TTL is tuned for data caching (minutes) expire before the retry window ends.
2. Verify the storage split: idempotency keys and data cache entries sharing one cache/namespace means short-TTL eviction silently disables replay protection.
3. Explain why testing missed it: local tests retry within seconds — well inside the TTL — while production retries land after eviction.
4. Prescribe the fix: a separate idempotency namespace with its own TTL budget (hours/day, matched to the client retry window), backed by shared CAS.
5. Name the verification: a QuarkusTest that moves past the TTL boundary (shortened TTL in test profile) and asserts the replay still returns the original result.

## Expected output

```
Diagnosis: idempotency keys live in the data cache (TTL 5m). A retry after the TTL
finds no key → treated as a new payment → duplicate charge.
Timing match: "a few minutes apart" ≈ the 5m eviction window.

Why tests missed it: test retries occur in seconds, inside the TTL.

Fix: separate namespace `idem:*` with TTL ≥ client retry window (24h), CAS-backed
via the shared Cache SPI implementation.

Verify: QuarkusTest with test-profile TTL (e.g., 2s): first call 201 → advance past
TTL → replay still resolves from the idempotency namespace, not re-executed.
```

## Failure the skill must avoid

"Raising the data-cache TTL to 30 minutes" as the fix. That wastes memory on data caching and still expires before long retry windows — idempotency storage needs its own namespace and TTL budget.
