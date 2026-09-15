# Example 2 — Read-only acknowledgment semantics review

## Prompt

> Ops found duplicate charges coming from requeued messages. Read-only review of our listener ack/retry logic on 6.7.x — where are we losing the guarantees?

## What the skill should do

1. Stay read-only; trace each listener's ack/nack sites with file and line evidence.
2. Check ack placement: ack must follow successful business processing, not message receipt. Receipt-acks plus a crash mid-processing produce exactly the replay-charge pattern ops observed.
3. Check the retry policy: unbounded retries without a dead-letter destination turn one poison message into an endless requeue loop that redelivers the same business effect.
4. Check message-id idempotency: the consumer-side dedup must use the shared CAS backend; a per-instance cache explains why duplicates appeared only with more than one replica.

## Expected output

| Listener | Ack site | Placement | Verdict |
|---|---|---|---|
| `PaymentListener` | `:47` | after commit | OK |
| `PaymentListener` | `:61` (requeue path) | nack without limit, no DLQ | VIOLATION — poison loop |
| `AnalyticsListener` | `:29` | on receipt, before processing | VIOLATION — loss on crash |
| Dedup backing | `IdempotencyStore.java:18` | Caffeine (per-JVM) | VIOLATION — not shared CAS |

Duplicate-charge chain: requeue loop (no DLQ) + per-instance dedup ⇒ the same message-id is processed on a second replica and charges again.

Plus: what was not verified (no broker test executed in this review).

## Failure the skill must avoid

Blaming the broker "delivering duplicates" and recommending consumer code ignore message ids. The duplicates are manufactured by the listener's own ack placement and per-instance dedup — the review must name those sites.
