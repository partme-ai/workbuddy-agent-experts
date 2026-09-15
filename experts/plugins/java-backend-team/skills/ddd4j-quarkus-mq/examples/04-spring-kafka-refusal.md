# Example 4 — Spring Kafka listeners in a Quarkus app

## Prompt

> Our team knows Spring Kafka inside out. Can we just add `spring-kafka` to our ddd4j-quarkus service and use `@KafkaListener`? Same broker, after all.

## What the skill should do

1. Draw the stack boundary: `@KafkaListener` belongs to Spring's container and its `ddd4j-boot-mq` world; the ddd4j-quarkus line wires brokers through its own `MQClient`/listener CDI model.
2. Explain why "same broker" is not the point: delivery semantics, ack handling, and lifecycle (drain, reverse-order close) are implemented by the adapter, and mixing two adapters means two uncoordinated lifecycle owners.
3. Refuse to blend the stacks — do not use this skill to wire Spring Kafka into Quarkus; if the team wants Spring Kafka, the project belongs on the Boot line.
4. Offer the productive path: reuse the team's semantics knowledge (retry limits, DLQ, dedupe) inside the ddd4j-quarkus listener model.
5. Name the native risk: Spring Kafka classes are not registered for the Quarkus native build; the mix fails at native build even when JVM mode runs.

## Expected output

```
Boundary: @KafkaListener is Spring-container machinery (ddd4j-boot-mq / Spring Boot).
The ddd4j-quarkus line wires Kafka/NATS through MQClient + listener CDI registration
with its own ack/retry/DLQ and lifecycle observers.

Why not to mix: two lifecycle owners over one broker client (drain/close conflicts),
and Spring Kafka classes are not registered for the Quarkus native build — JVM mode
"runs" while the native build fails.

Keep the knowledge, change the adapter: port your retry/DLQ/dedupe semantics into
the ddd4j-quarkus listener model shown in this skill's workflow.
```

## Failure the skill must avoid

Adding `spring-kafka` to the Quarkus service "as a pragmatic hack" and wiring both consumers. In production the two adapters drain/close in uncoordinated order, and the native build fails on unregistered Spring reflection.
