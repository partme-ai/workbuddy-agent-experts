---
name: ddd4j-boot-mq
description: Use when integrating ddd4j MQ adapters in Spring Boot, including broker auto-configuration, listener scanning, required or optional consumers, acknowledgment, retry, dead letter, readiness, and shutdown. 中文触发词：消息队列、多 Broker、Listener、ACK 确认、重试、死信、就绪检查、优雅关闭。
license: Apache-2.0
---

# ddd4j-boot MQ

## Overview

Covers Kafka, RabbitMQ, Pulsar, RocketMQ, ActiveMQ, MQTT, NATS, SQS, ONS/TDMQ, and listener lifecycle uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Choosing a broker adapter (Kafka, RabbitMQ, Pulsar, RocketMQ, ActiveMQ, MQTT, NATS, SQS, ONS/TDMQ) for a ddd4j-boot service, matched to delivery semantics and ordering needs.
- Wiring the MQ auto-configuration, listener registrar, and topic/tag/group/namespace settings on a specific Boot line (2.3–4.1).
- Deciding required versus optional listeners — whether a broker being down must block startup or degrade gracefully.
- Configuring acknowledgment, retry, and dead-letter policy, and verifying duplicates and recovery behavior.
- Auditing shutdown: producer/listener close must be idempotent, with an explicit resource owner and rollback.
- Diagnosing messaging failures: beans assembled but nothing consumed, listeners silently absent, or retries looping without reaching the dead letter.

## When NOT to Use

Do not use this skill when:

- **The `DomainEvent` publication contracts or event handler semantics need changing** — use `ddd4j-core` or `ddd4j-mq` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-mq`.
- **Generic auto-configuration mechanics are the question, not messaging** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The runtime is Spring Cloud Stream, Javalin, or Quarkus** — use `ddd4j-cloud-stream`, `ddd4j-javalin-mq`, or `ddd4j-quarkus-mq` instead; the Boot listener assembly does not transfer.
- **The project is plain Spring Boot without ddd4j** — generic Spring Kafka / Spring AMQP skills apply; the ddd4j listener registrar does not exist there.
- **The broker connection and its version pins are the question** — use `ddd4j-boot-bom` for ownership. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-bom`.
- **The Testcontainers/test-harness setup itself is being built** — use `ddd4j-boot-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-testing`.

## Trigger Keywords

**English**: message queue, multi-broker, listener, ACK acknowledgment, retry, dead letter, readiness, graceful shutdown

**中文**: 消息队列, 多 Broker, Listener, ACK 确认, 重试, 死信, 就绪检查, 优雅关闭
## Core Scope

Kafka, RabbitMQ, Pulsar, RocketMQ, ActiveMQ, MQTT, NATS, SQS, ONS/TDMQ, listener lifecycle.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among MQ implementations and Spring Boot assembly.
- Configuration, overrides, lifecycle, and verification.
- Maintenance-line compatibility judgments.

### ⚠️ Needs Input

- Target Boot line, POM, and configuration.
- Business behavior, dependencies, and deployment mode.
- Current test/CI/runtime evidence.

### ❌ Out of Scope

- Modifying ddd4j core public semantics.
- Substituting dependency or bean presence for real behavior.
- Unauthorized releases or production operations.

## Workflow

### Step 1: Confirm the source of truth

Run `ddd4j-boot-version-selection` to fix the line, then locate the MQ AutoConfiguration, its Properties, the listener registrar, and the corresponding `ddd4j-mq` modules on that line.

### Step 2: Select the broker

Match the broker to delivery semantics and ordering needs — at-least-once with retries is a different contract than exactly-once claims. Confirm topic/tag/group/namespace configuration and which listeners are required versus optional.

### Step 3: Verify the wiring

Check conditional wiring, default beans, and user bean override points. Confirm that a required listener's failure blocks startup, that retry/dead-letter policy is actually configured (not defaulted silently), and that producer/listener close is idempotent.

### Step 4: Test the delivery behavior

Execute context tests plus real broker round-trips (Testcontainers): publish/consume, ack, nack/retry, duplicates, recovery after broker loss, and graceful shutdown. Mark Docker-unavailable suites BLOCKED or SKIPPED — a skipped round-trip is not a pass.

### Step 5: Report with separated evidence

Report the chosen broker and adapter with configuration keys, the AutoConfiguration entry points, listener registrations, and override points, test results, and evidence state — configuration presence, bean creation, behavior, CI, and publish reported separately — plus risks and missing inputs.

## Gotchas

- A broker starter on the classpath proves nothing is consumed — listener scanning can find zero listeners and the context still starts green.
- "Required listener blocks startup" is a property to test, not assume: with the default off, a misconfigured topic surfaces as an empty consumer group in production instead of a failed deploy.
- A context that starts does not prove broker availability; bean creation and message delivery are different evidence layers.
- Retry without a dead-letter policy loops forever on a poison message and blocks the partition/queue — the absence fails silently until one bad payload arrives.
- Duplicates are normal under at-least-once redelivery; a consumer without an idempotency check passes the happy path and corrupts state on the first retry.
- A Docker-unavailable test suite that silently skips round-trips reports green while proving nothing — skips must be surfaced as BLOCKED/SKIPPED, not folded into pass counts.
- Printing MQ configuration for troubleshooting can leak broker endpoints and credentials — sensitive values must be redacted.

## Output and Exceptions

When information is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output credentials, tokens, production connection strings, or sensitive business data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；消息示例均为脱敏的虚构载荷。

## Quick Start

- "Use `$ddd4j-boot-mq` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-mq` to review existing usage against the current source."
- "Use `$ddd4j-boot-mq` to return an implementation choice, evidence state, and remaining risk."

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
