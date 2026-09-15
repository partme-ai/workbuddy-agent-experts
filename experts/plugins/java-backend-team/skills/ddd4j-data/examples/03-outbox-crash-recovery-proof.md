# Example 3 — Proving Outbox crash-recovery windows

## Prompt

> Our Outbox relay marks rows as sent, then publishes. Ops killed the pod mid-deploy last month and we lost two events. Design the verification that would have caught this.

## What the skill should do

1. Map the claim/send/confirm lifecycle and identify each crash window: after claim, after send, before confirm.
2. Require that "business write + event + Outbox row" share one transaction — verified first, because no relay design survives a split commit.
3. Specify crash-recovery tests for each window: kill after claim (row must be re-claimable), kill after send before confirm (redelivery must be tolerated by consumers), kill before claim (row stays pending).
4. Require idempotent consumption keyed on event/message id, since at-least-once delivery is the contract.
5. Run the tests against real containers with actual process kills, not simulated exceptions.

## Expected output

```
Lifecycle: claim → send → confirm (rows: PENDING → CLAIMED → SENT)

Window tests (Testcontainers + real kill -9):
  W1 kill after claim, before send   → row returns to PENDING after
                                        claim timeout; no loss
  W2 kill after send, before confirm → redelivery on restart; consumer
                                        deduplicates by event id
  W3 kill before claim               → row untouched, relay picks it up

Previous design's defect: SEND happened, then the sent-flag UPDATE —
kill in between = event delivered but marked unsent... or worse, the flag
written before the send: lost events, exactly what ops observed.

Evidence status: design SOURCE; window tests NOT RUN — this run is the gate.
```

## Failure the skill must avoid

Verifying with a mocked broker and try/catch "crash simulation." Real losses happen between two successful local operations — only real kill points exercise the windows.
