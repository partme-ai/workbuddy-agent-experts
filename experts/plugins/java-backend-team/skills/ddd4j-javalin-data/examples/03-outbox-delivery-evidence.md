# Example 3 — Proving Outbox delivery end to end

## Prompt

> We need evidence for the audit that "an order confirmed event always reaches the broker". Our Outbox is in PostgreSQL and the broker is external. What proof is possible?

## What the skill should do

1. Split the claim into its two separate concerns: business commit writes the Outbox row, and the delivery path publishes and acks it — neither proves the other.
2. Design the round-trip evidence: Testcontainers PostgreSQL plus a real broker; commit the command, wait for the relay, consume the message, and assert payload and dedup keys.
3. Cover the failure branches explicitly: relay crash between commit and publish (redelivery, dedup required), broker unavailability (retry with backoff), and duplicate consumption (message-id idempotency).
4. Report evidence tiers honestly — container runs executed versus `NOT RUN` — and mark any skipped branch explicitly.

## Expected output

```
Claim: confirmed order → event reaches broker.

Evidence (7.1.x, Testcontainers PostgreSQL + broker, EXECUTED):
  1. Commit → Outbox row present .......... PASS
  2. Relay publishes → consumer receives .. PASS (payload + message-id match)
  3. Relay killed after commit, restarted . PASS (redelivered once, dedup held)
  4. Broker stopped 30s ................... PASS (backoff, no loss)
  5. Duplicate delivery consumer-side ..... SKIPPED (consumer dedup owned by mq skill)

Caveat: MQ ack proves broker receipt; DB commit proves row only.
Neither alone satisfies the audit — the pair above does.

Evidence status: CONTAINER + BEHAVIOR tiers executed. CI tier NOT RUN for this SHA.
```

## Failure the skill must avoid

Answering "yes, the audit passes — the Outbox row is written in the same transaction". That proves persistence, not delivery; the audit claim was about the broker, and only the executed round-trip including relay-crash redelivery addresses it.
