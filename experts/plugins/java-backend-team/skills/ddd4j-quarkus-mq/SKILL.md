---
name: ddd4j-quarkus-mq
description: Use when integrating ddd4j MQ adapters with Quarkus, including Kafka, NATS, other brokers, acknowledgment, listeners, lifecycle, and Testcontainers. 中文触发词：消息集成、Kafka、NATS、Broker、ACK 确认、监听器、重试死信、生命周期、容器测试。
license: Apache-2.0
---

# ddd4j-quarkus MQ

## Overview

Covers Kafka, NATS, other current brokers, ACK, listeners, lifecycle, and Testcontainers uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Integrating Kafka or NATS (and other brokers the current line supports) with ddd4j MQ adapters on Quarkus.
- Registering `MQClients` and listeners via CDI with explicit required/optional semantics.
- Implementing ack-after-business-success, nack with policy-driven requeue, retry limits, and dead letters.
- Owning listener lifecycle: startup/shutdown observers, drain, reverse-order close, idempotent close.
- Running Testcontainers round-trips — publish/consume, headers, ack/nack/retry, duplicates, recovery.
- Reviewing messaging wiring and delivery semantics on the 3.3.x or 4.0.x line.

## When NOT to Use

Do not use this skill when:

- **Spring Boot messaging (Spring Kafka, annotation listeners)** — use `ddd4j-boot-mq` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-mq`; Spring Kafka listeners must not be mixed into a ddd4j-quarkus line.
- **Spring Cloud Stream bindings** — use `ddd4j-cloud-stream` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-stream`.
- **Javalin messaging** — use `ddd4j-javalin-mq` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-mq`.
- **The event publication contracts themselves (DomainEvent publication rules)** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Generic CDI wiring of the MQ clients with no broker semantics** — use `ddd4j-quarkus-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-runtime`.
- **The project is a plain Quarkus app without ddd4j** — generic Quarkus messaging guidance applies; do not use the ddd4j MQClient model on a non-ddd4j stack.

## Trigger Keywords

**English**: messaging integration, Kafka, NATS, broker, ACK acknowledgment, listener registration, retry dead letter, lifecycle drain, Testcontainers

**中文**: 消息集成, Kafka, NATS, Broker, ACK 确认, 监听器, 重试死信, 生命周期, 容器测试

## Core Scope

Kafka, NATS, other current brokers, ACK, listeners, lifecycle, Testcontainers.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for messaging and Quarkus adaptation.
- CDI, build-time, and runtime boundaries.
- Differences between the two maintenance lines.

### ⚠️ Needs Input

- Target line, POM, and Quarkus Platform.
- Capabilities, runtime, and deployment requirements.
- Current source/test/CI evidence.

### ❌ Out of Scope

- Substituting the Spring assembly model for Quarkus.
- Treating a BOM import as a registered bean.
- Unauthorized releases or production changes.

## Workflow

### Step 1: Confirm the source of truth

Fix the line via `ddd4j-quarkus-version-selection`, then locate `ddd4j-quarkus-mq` and the broker tests in that checkout. The supported brokers and listener idioms are per line.

### Step 2: Select and register the broker

Match the broker to the delivery semantics you need and confirm what the current line actually supports, then register `MQClients` and listeners via CDI with explicit required/optional semantics.

### Step 3: Implement reliability and lifecycle

Ack after business success; nack with policy-driven requeue, retry limits, and dead letters. Bind startup/shutdown observers with drain, reverse-order close, and idempotent close.

### Step 4: Test with real brokers

Run Testcontainers round-trips covering publish/consume, headers, ack/nack/retry, duplicates, and recovery. When Docker is unavailable, mark the suites BLOCKED/SKIPPED — never PASS.

### Step 5: Report

Produce a single report: broker and adapter choices with configuration keys, listener registrations and lifecycle owners, tests executed and evidence state per tier, and risks with proposed fixes and missing inputs.

## Gotchas

- Ack must follow business success, not message receipt — acking on arrival loses the event whenever the handler throws after the ack.
- Duplicate deliveries are normal broker behavior; consumer idempotency must be explicit, and a "processed once" assumption fails on the first redelivery.
- Testcontainers round-trips are the only real broker proof; an embedded or mocked broker validates wire format only, not consumer semantics.
- Quarkus's Docker detection is special across its multiple classloaders; an unavailable Docker run must be reported BLOCKED/SKIPPED, never folded into PASS.
- Listener lifecycle belongs in startup/shutdown observers with drain and reverse-order close — closing a shared client while a consumer is mid-batch loses or duplicates the batch.
- A BOM import of the MQ extension registers no `MQClient`; CDI producers and build steps do, so "we imported the mq artifact" is not wiring evidence.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；Broker 连接信息示例均为脱敏占位符。

## Quick Start

- "Use `$ddd4j-quarkus-mq` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-mq` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-mq` to return an implementation choice, evidence state, and remaining risk."

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
