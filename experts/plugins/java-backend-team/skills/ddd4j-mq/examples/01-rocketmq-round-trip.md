# Example 1 — RocketMQ producer/consumer with ack, retry, and DLQ

## Prompt

> We're on ddd4j 2.0.x and picked RocketMQ for order events. Set up the consumer side properly: it must survive handler crashes, retry a few times, and never lose or double-process an order event.

## What the skill should do

1. Confirm the delivery contract first: at-least-once with per-key ordering — everything else follows from it.
2. Build the listener on `MQListener`/`MQEvent` with `Acknowledgment`, acking only after business processing succeeds.
3. Configure retry: recorded attempts, backoff, upper bound, then dead-letter entry.
4. Make consumption idempotent by message/event id, since at-least-once guarantees redelivery.
5. Check destination naming against RocketMQ's character rules before anything ships.
6. Specify the round-trip and recovery tests against Testcontainers RocketMQ.

## Expected output

```
Consumer contract (order-events topic, group order-service):
  - MQListener<OrderEvent> processes, then ack succeeds → ack AFTER business
  - business exception → nack → retry (backoff 1s/5s/25s, max 3)
  - exhausted → dead-letter topic order-events-DLQ, alert fires
  - idempotency: dedupe on message id + event id before processing
  - destination name checked against RocketMQ rules (no illegal chars)

Tests (Testcontainers RocketMQ):
  1. publish → consume → ack             (round-trip)
  2. handler throws ×3 → DLQ entry
  3. redelivered duplicate → processed once
  4. kill consumer mid-processing → redelivery, no loss
Status: design SOURCE; container tests NOT RUN.
```

## Failure the skill must avoid

Wiring ack immediately on receipt "so we don't lose messages" plus a broad try/catch "so nothing crashes." That combination loses messages on crash-after-ack and hides failures from the DLQ — the two canonical MQ defects in one config.
