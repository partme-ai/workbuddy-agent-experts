---
name: ddd4j-mq
description: Use when choosing, implementing, or reviewing ddd4j messaging with Kafka, RabbitMQ, Pulsar, RocketMQ, ActiveMQ, Artemis, MQTT, NATS, SQS, ONS, TDMQ, Redis Stream, Spring integration, acknowledgments, retries, dead letters, or lifecycle. 中文触发词：消息队列、Broker 选型、ACK 确认、重试与死信、幂等消费、监听器生命周期、RocketMQ、Kafka。
license: Apache-2.0
---

# ddd4j MQ

## Overview

All broker adapters unify onto MQClient, MQListener, MQEvent, and Acknowledgment; choose delivery and operational semantics first, then the broker.

## When to Use

- Selecting a broker against delivery semantics: Kafka, RabbitMQ, Pulsar/TDMQ, RocketMQ/ONS, ActiveMQ/Artemis, MQTT, NATS, SQS, Redis Stream, or in-process Disruptor.
- Implementing producers/consumers on the unified `MQClient`, `MQListener`, `MQEvent`, and `Acknowledgment` API.
- Designing ACK/NACK policy: ack after successful business processing, requeue or dead-letter on failure.
- Configuring retries with backoff, an upper bound, and dead-lettering.
- Handling listener lifecycle: required listeners blocking startup on failure, partial-failure rollback, idempotent close.
- Verifying real publish→consume→ack round-trips with Testcontainers.

## When NOT to Use

Do not use this skill when:

- **The transactional Outbox on the database side is the question** — use `ddd4j-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-data`; this skill assumes a reliable bridge exists and consumes its events.
- **Redis used as a cache rather than Redis Stream as a broker is the question** — use `ddd4j-cache` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cache`.
- **The HTTP endpoint that triggers publishing is the question** — use `ddd4j-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-web`.
- **Generic Spring Kafka / RabbitMQ annotation usage with no ddd4j unification involved** — use the framework's own skills; do not map `MQClient` semantics onto an unrelated setup.
- **A request treats a started broker container as proof of a working message chain, or mocks as proof of durability** — do not use this skill to endorse that; round-trip evidence is the standard here.
- **Mechanically unifying topic/destination names across brokers is requested** — naming converts per broker rule (e.g. RocketMQ destination character restrictions), not by find-and-replace.

## Trigger Keywords

**English**: message queue, broker selection, ACK acknowledgment, retry dead letter, idempotent consumer, listener lifecycle, Kafka, RocketMQ

**中文**: 消息队列, Broker 选型, ACK 确认, 重试与死信, 幂等消费, 监听器生命周期, Kafka, RocketMQ

## Broker Routing

| Requirement | Candidates |
|---|---|
| High-throughput logs/streams | Kafka |
| AMQP routing | RabbitMQ |
| Multi-tenant streams/queues | Pulsar/TDMQ |
| Domestic transactional/ordered messages | RocketMQ/ONS |
| JMS | ActiveMQ/Artemis |
| IoT | MQTT/Mica MQTT |
| Lightweight JetStream | NATS |
| AWS | SQS |
| Redis infrastructure | Redis Stream |
| In-process | Disruptor |
| Spring Cloud | unified by the Cloud Stream adapter |

## Core Rules

1. Required listeners that fail initialization must block startup; optional ones may degrade readiness.
2. Ack after successful business processing; on failure nack/requeue according to policy.
3. Retries need backoff, an upper bound, and dead-lettering.
4. Message id/business key drives idempotency; never rely on the broker alone.
5. Partial initialization failure must shut down already-created resources in reverse order.
6. close is idempotent; threads, consumers, producers, and connections all have owners.
7. Configurations such as persist=true must have behavior tests.

## Capability Boundaries

### ✅ Strong At

- Broker selection and the unified API.
- ACK/NACK, retries, dead letters, idempotency.
- Listener scanning and lifecycle.
- Testcontainers round-trips.

### ⚠️ Needs Input

- Broker, delivery semantics, and ordering requirements.
- topic/tag/group/namespace.
- Deployment and disaster-recovery model.

### ❌ Out of Scope

- Declaring the message chain successful because a container started.
- Using mocks to prove broker durability.
- Mechanically unifying topic naming across brokers.

## Workflow

### Step 1: Define delivery semantics and ordering

Decide at-most-once vs at-least-once and whether ordering matters per stream. Every later choice — ack timing, retry policy, idempotency — derives from this decision.

### Step 2: Choose the broker and adapter

Match the requirement matrix to a broker (high-throughput streams → Kafka; AMQP routing → RabbitMQ; transactional/ordered → RocketMQ; JMS → ActiveMQ/Artemis; lightweight → NATS; etc.), then confirm the ddd4j adapter module exists for the line and that its `Properties`, `MQClient`, and header mapping are read from source.

### Step 3: Configure producer, consumer, and listener

Set topic/tag/group/namespace per broker rules, register listeners, and mark each as required (must block startup on failure) or optional (may degrade readiness). Configure destination names within each broker's character rules.

### Step 4: Verify the publish→consume→ack round-trip

Prove a real message travels the full chain: publish, consume by `MQListener`, business processing, then `Acknowledgment` — against a real broker container, not a started-but-idle one.

### Step 5: Verify retry, dead-letter, duplicates, and recovery

Cover business-exception nack per policy, retry with backoff and an upper bound, dead-letter entry after exhaustion, and duplicate delivery handled by idempotent consumers keyed on message/event id.

### Step 6: Verify lifecycle

Prove a required listener's startup failure blocks readiness, partial initialization shuts down already-created resources in reverse order, and `close` is idempotent — threads, consumers, producers, and connections all have named owners.

## Gotchas

- ACK completed before business processing — a crash after the ack but before the work loses the message with zero broker-side evidence; ack belongs after processing succeeds.
- Consumed-message failures swallowed by a broad catch — the container stays healthy, the dead letter never fills, and the message is gone; failures must nack per policy.
- A required consumer failing at startup while the application still reports READY — readiness must aggregate listener state, not just bean creation.
- Counting a broker container start as a round-trip — Testcontainers "connection established" proves nothing until a message completes publish→consume→ack.
- Illegal characters in RocketMQ destinations — topic/destination naming rules differ per broker; a name valid on Kafka can be rejected at RocketMQ send time.
- Skipped tests written down as PASS — an unrun broker matrix recorded as green is indistinguishable from a real one in the release notes, which is why evidence states are explicit.
- Closing only the consumer on shutdown — producers, connections, and threads each have owners and must close in reverse initialization order; `close` must also be idempotent for repeated shutdown paths.

## Deep Reference

- [Broker Matrix](references/broker-matrix.md)
- [ACK and Reliability](references/ack-retry-dead-letter.md)
- [Lifecycle](references/lifecycle.md)
- [Testing](references/testcontainers.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Message payloads, headers, and logs must not leak tokens, PII, or cloud access keys. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；消息示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-mq` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-mq` to review existing usage against the current source."
- "Use `$ddd4j-mq` to return an implementation choice, evidence state, and remaining risk."

## Audience and Customization

- Developers: provide the target maintenance line, POM, capabilities, and acceptance behavior.
- Architects: specify a read-only boundary review, compatibility, or migration target.
- Testers / release engineers: specify the required evidence levels; do not auto-expand to release or production operations.

Customize the target framework, allowed implementations, excluded modules, compatibility requirements, and output evidence level. When input is insufficient, give a tentative verdict first, then list "missing: specific item; how to provide: required path or configuration".

## FAQ

1. **Are skills organized by Maven artifact?** No — by the user-facing capability domain.
2. **Can I copy another maintenance line directly?** No — verify the version and source first.
3. **Does a class existing in source prove the capability works?** No — registration and behavior evidence are also required.
4. **How do I report tests that did not run?** Mark `NOT RUN` or `BLOCKED`.
5. **Can the skill commit or release automatically?** Only after explicit user authorization.
6. **What if the implementation is missing?** Describe the missing module or evidence; do not invent APIs.
