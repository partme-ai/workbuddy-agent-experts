# Example 3 — Proving duplicate delivery is handled across instances

## Prompt

> The message bus vendor guarantees at-least-once, so duplicates WILL happen. Give me test evidence that our 7.1.x service survives them — actually run it, including with two instances.

## What the skill should do

1. Fix the line and locate the listener inventory plus the dedup wiring (which backend backs message-id idempotency on the production profile).
2. Execute the duplicate contract against a real broker: deliver the same message-id twice sequentially and concurrently, with processing that commits a business effect; assert the effect happened exactly once.
3. Run the cross-instance case: two service instances consuming while the same id is delivered to both — this is where per-instance dedup fails and shared CAS must hold.
4. Cover the recovery branches: duplicate arriving while the first is still in-flight (CAS contention), and after the first completed (replay path). Report evidence tiers honestly.

## Expected output

```
Evidence: at-least-once duplicate handling on 7.1.x (SHA abc123)

| Case                                        | Expected       | Actual         | State |
|---------------------------------------------|----------------|----------------|-------|
| Same id, sequential redelivery              | effect ×1      | effect ×1      | PASS  |
| Same id, two instances concurrent           | effect ×1      | effect ×1      | PASS  |
| Same id while first still in-flight         | one winner, one CAS-retry | one winner | PASS |
| Same id after completion                    | replay ack, no effect | replay ack | PASS |
| CAS backend down during delivery            | explicit failure, no effect | effect created | FAIL |

FAIL: dedup falls through when the shared CAS is unreachable (DedupFilter.java:55).
Fix: fail closed (nack + retry) when CAS is unavailable; add contract test.
Container/behavior tier EXECUTED against real broker; CI tier NOT RUN.
```

## Failure the skill must avoid

Reporting "duplicates are handled, we dedup by message id" from a single-instance sequential test. At-least-once means the concurrent cross-instance case is the norm, and the CAS-outage fall-through is the duplicate factory the evidence run just exposed.
