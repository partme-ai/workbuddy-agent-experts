# Example 4 — Boundary: mocks offered as durability proof

## Prompt

> The Kafka broker won't run in our CI — security team blocked containers. QA suggests we mock `MQClient` and the listener and call the reliability story done: "the logic is the same, right?" Also, just reuse the Kafka topic names on RocketMQ for the new region, they're already documented.

## What the skill should do

1. Refuse the mock-as-proof plan for the durability claim: a mock executes your code, not the broker's delivery, persistence, retry, or redelivery semantics — exactly the parts the claim is about. Unit tests with mocks are fine for logic; they cannot grade "reliable."
2. Name what would constitute real evidence despite the CI constraint: a broker run outside CI (staging job, nightly pipeline with container access, or a managed-broker staging namespace) with the round-trip + failure-injection runs recorded as CI/BLOCKED in the interim.
3. Refuse the mechanical topic-name reuse: destination naming converts per broker rule — RocketMQ enforces its own character/length rules, and a Kafka-valid name can fail at send time or collide with naming conventions.
4. Record evidence states honestly rather than upgrading BLOCKED to PASS.

## Expected output

```
Refusal 1 (mock = durability proof): mocks validate call ordering in your
code. Delivery guarantees live in the broker. Claim recorded as BLOCKED, not
PASS, until a real-broker run exists (staging/nightly container job).

Refusal 2 (topic names copied to RocketMQ): names convert per broker rules —
validate against RocketMQ destination constraints and re-derive names, do not
find-and-replace across brokers.

What CAN ship now: unit-level handler tests (logic only), with the release
note stating broker behavior UNVERIFIED.
```

## Failure the skill must avoid

Writing "reliability verified via mocked broker" into the release notes. That converts an infrastructure gap into a false claim — the exact evidence fraud the MQ skill's gate exists to catch.
