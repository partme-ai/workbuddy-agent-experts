# Example 1 — Kafka consumer with retry and dead-letter

## Prompt

> We're on ddd4j-quarkus 3.3.x and need a Kafka consumer for payment events. If handling fails, retry three times then park the message. How do we build it?

## What the skill should do

1. Fix the line (3.3.x → Quarkus Platform 3.37.4 / ddd4j 2.0.x / JDK 17 / Maven 3) and read the MQ adapter in that checkout to confirm Kafka support and listener idioms.
2. Register the `MQClient` and listener via CDI with required semantics so a missing broker fails startup loudly.
3. Implement ack after business success only; on failure, nack with a retry policy (3 attempts, backoff) and a dead-letter destination.
4. Make the consumer idempotent — redeliveries are normal, so side effects need a dedupe key.
5. Bind lifecycle in startup/shutdown observers: drain in-flight messages, close after consumers stop, idempotent close.

## Expected output

```
Listener: PaymentEventListener (CDI, required) → topic payment.events
Policy: ack after handler commit; nack → retry x3 (backoff 1s/2s/4s) → dead-letter topic
        payment.events.dlq with original headers + failure reason.
Idempotency: dedupe on eventId via CAS before applying side effects.
Lifecycle: shutdown observer drains in-flight, then closes consumer, then client
          (reverse order, idempotent).

Tests (Testcontainers Kafka): publish/consume round-trip; handler failure → 3 retries
→ DLQ; redelivery of already-applied event → no duplicate side effect.
```

## Failure the skill must avoid

Acknowledging the message when it arrives and handling it afterward "for throughput". A handler crash after ack permanently loses the payment event — the retry/DLQ policy never sees it.
