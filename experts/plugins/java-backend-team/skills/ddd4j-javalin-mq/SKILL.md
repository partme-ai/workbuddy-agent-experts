---
name: ddd4j-javalin-mq
description: Use when wiring ddd4j MQ clients and listeners into Javalin lifecycle, including required or optional consumers, acknowledgment, retry, readiness, rollback, and shutdown. 中文触发词：MQ Listener、ACK 确认、重试、死信队列、消息幂等、就绪检查、优雅关闭。
license: Apache-2.0
---

# ddd4j-javalin MQ

## Overview

Covers MQClient, listeners, required/optional, ACK, retry, readiness, rollback, and close uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Registering MQ clients and listeners as `JavalinLifecycleParticipant`s with explicit required-versus-optional classification on 6.7.x, 7.1.x, or 7.2.x.
- Implementing the readiness contract: required-consumer failure blocks startup or readiness, optional-consumer failure degrades status explicitly.
- Implementing acknowledgment semantics — ack after successful business processing, nack with policy-driven requeue — plus backoff, retry limits, dead-letter routing, and message-id idempotency.
- Managing MQ shutdown: stop receiving, drain, and close consumers/connections in reverse registration order with idempotent close.
- Running publish/consume, ack/nack/retry, duplicate, recovery, and shutdown behavior tests against a real broker.

## When NOT to Use

Do not use this skill when:

- **The Outbox relational side is the question (writing Outbox rows in the business transaction, relay ownership in the data module)** — use `ddd4j-javalin-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-data`.
- **Lifecycle participant mechanics themselves (ordering, rollback, hooks) are the question** — use `ddd4j-javalin-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-runtime`.
- **Domain event contracts (`DomainEvent`, publication, replay) are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **A cross-capability review or release gate is needed** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **Spring Boot, Quarkus, or Spring Cloud messaging is the question** — use `ddd4j-boot-mq`, `ddd4j-quarkus-mq`, or `ddd4j-cloud-stream` instead, for example Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-mq`.
- **The project consumes from a broker with a plain Javalin app without ddd4j** — do not use this skill; use `java-skills` instead, since the `MQClient` lifecycle contract does not exist there.

## Trigger Keywords

**English**: MQ listener, acknowledgment, retry, dead letter, message idempotency, readiness, graceful shutdown

**中文**: MQ Listener, ACK 确认, 重试, 死信队列, 消息幂等, 就绪检查, 优雅关闭

## Core Scope

MQClient, listeners, required/optional, ACK, retry, readiness, rollback, close.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for messaging and Javalin adaptation.
- Lifecycle, configuration, and behavior boundaries.
- Differences across the three maintenance lines.

### ⚠️ Needs Input

- Target branch, POM, and Javalin version.
- Business behavior, dependencies, and deployment mode.
- Current source/test/CI evidence.

### ❌ Out of Scope

- Copying Javalin 6 code directly to 7.
- Substituting smoke tests for real behavior.
- Unauthorized releases or production changes.

## Workflow

### Step 1: Confirm the source of truth

Fix the maintenance line with `ddd4j-javalin-version-selection`, then locate the MQ module, its listener registrations, and the lifecycle tests in the current checkout.

### Step 2: Wire listeners into the lifecycle

Register `MQClient`s as lifecycle participants with an explicit required or optional classification. Confirm required-consumer failure blocks startup while optional failure degrades readiness explicitly — never a silent READY.

### Step 3: Implement reliability

Ack only after successful business processing; nack with a policy-driven requeue. Add backoff, retry limits, dead-letter routing, and message-id idempotency so duplicates and poison messages terminate in a defined state.

### Step 4: Manage shutdown

Stop receiving, drain in-flight messages, and close consumers/connections in reverse registration order. Confirm close is idempotent across repeated shutdowns and embedded-test cycles.

### Step 5: Verify with a real broker

Run publish/consume, ack/nack/retry, duplicate, recovery, and shutdown behavior tests. Produce a report with the listener inventory, evidence state per tier, and remaining risk.

## Gotchas

- Required-consumer failure must block startup while optional-consumer failure degrades readiness explicitly — a silently READY optional consumer hides a broken integration until the first business request needs it.
- Ack belongs after successful business processing, not on receipt; acking on receipt converts a crash mid-processing into permanent message loss.
- Retry without limits or dead-letter routing turns one poison message into an infinite redelivery loop that also starves healthy traffic.
- Message-id idempotency across instances requires the shared CAS backend — Caffeine deduplicates only within one JVM.
- `JavalinLifecycleParticipant` shutdown runs in reverse registration order; consumers registered early must close last, and close must be idempotent.
- A broker container starting is not consumer behavior passing — duplicate, recovery, and shutdown paths need executed tests, not a green container.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；消息示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-mq` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-mq` to review existing usage against the current source."
- "Use `$ddd4j-javalin-mq` to return an implementation choice, evidence state, and remaining risk."

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
