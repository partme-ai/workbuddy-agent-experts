# Example 5 — Diagnosing silently vanished messages

## Prompt

> Occasionally an order confirmation email just never goes out. Logs show the consumer picked the message up, then nothing — no error, no retry, nothing in the dead letter. The broker dashboard says everything was acknowledged. Where did our messages go?

## What the skill should do

1. Match the signature — consumed, acknowledged, no error, no retry, no DLQ — to premature acknowledgment: the ack fired before or instead of the business work.
2. Locate the ack call in the listener and compare its position with the email-send boundary.
3. Identify the typical variants: ack in a `finally`, ack in a framework callback that fires on receipt, or a broad catch that logs-and-acks on business failure.
4. Prescribe the fix: ack strictly after successful processing; business failure → nack → retry policy → DLQ.
5. Define the regression test: a handler that throws must produce a retry then a DLQ entry — and a handler that crashes mid-processing must not leave the message acknowledged.

## Expected output

```
Diagnosis: premature ack.

Evidence trail:
  - Broker: message acknowledged (dashboard)  ← consistent with report
  - Listener code: channel.basicAck(...) in finally block, BEFORE the send
    result is checked; email-client exception caught and logged
  → failure path = log + ack. No retry, no DLQ. Message gone.

Fix:
  1. ack only after the business send succeeds
  2. business failure → nack → retry (backoff, bound) → DLQ
  3. remove the swallow-catch

Regression test: throwing handler → message requeued, then DLQ after bound;
crash-injected handler → message redelivered on restart. Status: NOT RUN.
```

## Failure the skill must avoid

Chasing the email provider or the broker dashboard "for the lost messages." The broker's view is clean because the ack was premature — the loss happened on the consumer side, and only the ack-position fix closes it.
