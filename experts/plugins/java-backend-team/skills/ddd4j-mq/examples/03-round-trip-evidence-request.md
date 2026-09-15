# Example 3 — Demanding real round-trip evidence

## Prompt

> The integration report says "Kafka integration verified — Testcontainers green." Before I sign the release, what exactly did that test do? I've been burned by this before.

## What the skill should do

1. Treat the claim as ungraded until the test's assertions are inspected — distinguish container-started, connection-established, and full publish→consume→ack.
2. Read the test source: does a message actually travel from producer through `MQListener` to a business assertion, or does the test only assert the consumer bean exists?
3. Check whether failure paths were exercised (handler exception → nack → retry/DLQ) or only the happy path.
4. Re-grade the evidence: container start alone is not a round-trip; a happy-path round-trip is not a reliability proof.
5. State precisely which additional runs would upgrade the claim.

## Expected output

```
Claim under review: "Kafka integration verified — Testcontainers green"

Test inspection (SOURCE of the test class):
  - asserts KafkaContainer started and consumer bean registered
  - sends NO message; consumes NOTHING
  → evidence grade: CONTAINER-START only. Round-trip NOT exercised.

Needed to support "integration verified":
  1. publish real event → MQListener receives → business assertion passes
  2. handler-exception run → nack → retry recorded → DLQ after bound
  3. duplicate delivery run → idempotent consumer processes once

Verdict: release sign-off withheld pending runs 1–3. Evidence reclassified:
TEST (container start) only.
```

## Failure the skill must avoid

Accepting "Testcontainers green" as a round-trip proof. A started container with zero messages sent is the most common false evidence in MQ integration reports — reading the test's assertions is the only way to know.
