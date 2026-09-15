# Example 3 — Proving replay behavior for an idempotent endpoint

## Prompt

> Give me evidence that our POST /api/orders with the same idempotency key doesn't create two orders. Test it, don't just read the code.

## What the skill should do

1. Fix the line and locate the HTTP contract tests plus the idempotency wiring (which backend backs the key check on this deployment profile).
2. Execute the replay contract: same key twice, sequential; then concurrent; then from a second instance against the shared backend — assert order count stays at one and the replayed request gets the original response.
3. Exercise the edge paths: missing key (agreed error status), different key on semantically identical payload (two orders — document that as expected).
4. Report evidence tiers: which cases executed against the shared CAS backend and which, if any, were skipped.

## Expected output

```
Evidence: POST /api/orders idempotent replay (7.2.x, SHA abc123)

| Case                              | Expected          | Actual            | State |
|-----------------------------------|-------------------|-------------------|-------|
| Key K, first                      | 201, 1 order      | 201, 1 order      | PASS  |
| Key K, replay sequential          | original response | original response | PASS  |
| Key K, two instances concurrent   | 1 order total     | 1 order total     | PASS  |
| No key                            | 400 + error body  | 400 + error body  | PASS  |
| Key K on CAS backend down         | explicit 5xx      | order created     | FAIL  |

FAIL root cause: CAS failure path falls through to processing (IdempotencyFilter.java:63).
Fix: fail closed with 503 when the CAS is unavailable; add contract test.
Container/behavior tier EXECUTED; CI tier NOT RUN for this SHA.
```

## Failure the skill must avoid

Reporting "replay is covered, the filter returns the stored response" from a single-instance sequential test. The cross-instance concurrent case and the CAS-failure path are where duplicates actually happen — one green row is not replay evidence.
