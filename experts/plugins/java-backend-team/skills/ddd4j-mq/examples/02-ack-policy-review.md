# Example 2 — ACK / retry / idempotency review (read-only)

## Prompt

> Audit our messaging setup before the capacity review. I want to know where messages can silently vanish or get processed twice. Kafka and RabbitMQ both in the mix.

## What the skill should do

1. Stay read-only — findings only.
2. For every listener, locate the ack site and compare it to the business-processing boundary.
3. Check failure handling: does a business exception nack per policy, or is it swallowed by a catch?
4. Check retry configuration: backoff, upper bound, and dead-letter destination actually wired.
5. Check idempotency: is consumption deduplicated by message/event id, or does it trust broker exactly-once?
6. Check the two-broker split: Spring listener vs ddd4j unified API usage, and per-broker destination validity.

## Expected output

| Listener | Ack position | Failure path | Retry/DLQ | Idempotent | Verdict |
|---|---|---|---|---|---|
| `OrderKafkaListener` | after processing | nack per policy | yes | yes | OK |
| `PaymentRabbitListener` | on receipt ← | broad catch, logged | none | no | critical |
| `StockRedisStreamListener` | after processing | nack | retry, no DLQ topic configured | yes | medium |

Additional finding: the Rabbit destination contains a `*` wildcard in production config — valid in some tooling, ambiguous in AMQP binding semantics. Evidence: SOURCE only; no broker exercised.

## Failure the skill must avoid

Reporting "messaging looks solid" because all listeners are registered and consuming in staging. The ack-on-receipt listener is lossy by construction and only a failure-injection test would ever show it.
