# Example 5 — Lost messages after consumer crash

## Prompt

> Since last week's "performance fix", we silently lose payment events whenever the handler throws. Nothing shows in the DLQ. What did the fix break?

## What the skill should do

1. Diff the suspect commit and look for the ack path moving: ack-on-receipt before the handler runs is the classic cause of silent loss.
2. Confirm the sequence: with ack moved before business success, a handler throw acks a message that was never processed — the broker will not redeliver, and the DLQ policy never fires.
3. Restore the contract: ack after business success (handler commit), nack into the retry policy with limits, then dead-letter.
4. Check the loss is not compounded by missing consumer idempotency once redelivery resumes — previously-acked-but-unprocessed events may also have to be reconciled.
5. Name the verification: a Testcontainers round-trip where the handler throws on the first attempt, asserting redelivery and eventual DLQ placement.

## Expected output

```
Diff finding (commit abc123): ack moved from after-handler to on-receive
"to avoid redelivery storms".

Consequence: handler throws → message already ACKed → broker considers it done →
no redelivery, no DLQ entry. Matches the silent-loss report.

Fix: restore ack-after-business-success; keep the retry policy (x3, backoff) and
DLQ as the terminal path.
Reconciliation: audit the loss window for acked-but-unprocessed events.
Verify: Testcontainers case — handler throws on attempt 1 → redelivered → attempt 2
succeeds; handler always-fails → DLQ after 3 retries.
Evidence: SOURCE diff + TEST pending.
```

## Failure the skill must avoid

"Fixing" the loss by only enlarging the retry count. With ack-on-receipt, retries never happen at all — the ack semantics are the defect, not the retry policy.
