# Example 1 — Kafka listeners with retry and dead letter

## Prompt

> Our Boot 3 ddd4j service needs to consume order events from Kafka. At-least-once is fine, but a bad message must never wedge the consumer. Wire it up through ddd4j-boot.

## What the skill should do

1. Fix the maintenance line, then read the MQ AutoConfiguration, Properties, and listener registrar on that line.
2. Assemble the Kafka adapter via the boot MQ module; register the listeners through the ddd4j listener scanning, not ad-hoc `@KafkaListener` copies.
3. Configure the delivery contract: at-least-once ack, bounded retry, then dead letter — a poison message must leave the main path.
4. Make the order-events listener a required listener so a broker/topic misconfiguration blocks startup instead of silently consuming nothing.
5. Prove with Testcontainers round-trips: publish/consume, retry, dead-letter arrival, duplicate delivery, and graceful shutdown.

## Expected output

```
Selection: Kafka adapter on line 3.x, listeners via ddd4j-boot listener
registrar (single scanning path).

Delivery contract:
  ack mode: at-least-once
  retry: bounded, then dead-letter topic   ← configured explicitly
  required listener: yes — startup fails if the topic is not resolvable

Testcontainers evidence:
  publish/consume            PASS
  poison message → DLQ       PASS (main consumer continues)
  redelivery duplicate seen  PASS (consumer idempotency check works)
  broker loss + recovery     PASS
  shutdown: listeners closed, no in-flight loss   PASS

Evidence: behavior TEST RUN (Testcontainers). CI: NOT RUN.
```

## Failure the skill must avoid

Leaving retry unbounded with no dead letter because "Kafka redelivers anyway". The first malformed payload then spins the consumer forever and the partition stops moving — the exact wedge this contract prevents.
