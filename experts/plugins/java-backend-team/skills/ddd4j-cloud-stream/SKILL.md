---
name: ddd4j-cloud-stream
description: Use when integrating ddd4j-cloud Spring Cloud Stream with StreamBridge, function and binding names, physical destinations, acknowledgment, Kafka, RabbitMQ, Pulsar, or RocketMQ. 中文触发词：消息集成、绑定、目的地、消息确认、死信、Kafka、RabbitMQ、RocketMQ。
license: Apache-2.0
---

# ddd4j-cloud Stream

## Overview

Covers StreamBridge, function/binding/destination, ACK/NACK, Kafka, RabbitMQ, Pulsar, and RocketMQ uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Mapping functions, binding names, and physical destinations per broker (Kafka, RabbitMQ, Pulsar, RocketMQ).
- Publishing with `StreamBridge` and wiring consumer ACK/NACK with retry and dead-letter policy.
- Propagating Context/Tenant into message headers and restoring them on consume.
- Applying the line's `BindingNamingContributor` naming rules.
- Diagnosing messages that are never consumed, duplicated, or lost on redelivery.
- Verifying broker integration with real publish/consume, ack/nack/retry, duplicates, and recovery runs.

## When NOT to Use

Do not use this skill when:

- **Synchronous request/response between services is the need** — use `ddd4j-cloud-feign` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-feign`.
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-mq` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-mq`.
- **Broker/adapter choice at the ddd4j level is the question** — use `ddd4j-mq` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-mq`.
- **The runtime is Javalin or Quarkus** — use `ddd4j-javalin-mq` or `ddd4j-quarkus-mq` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-mq` (or `--skill ddd4j-quarkus-mq`).
- **Generic Spring Cloud Stream without ddd4j** — do not use this skill; apply generic `spring-cloud` guidance instead (no install command).
- **Database writes and transactions are the question** — use `ddd4j-cloud-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-data`.

## Trigger Keywords

**English**: message integration, StreamBridge, binding name, physical destination, ACK, dead letter, Kafka, RocketMQ

**中文**: 消息集成, 绑定, 目的地, 消息确认, 死信, Kafka, RabbitMQ, RocketMQ

## Core Scope

StreamBridge, function/binding/destination, ACK/NACK, Kafka, RabbitMQ, Pulsar, RocketMQ.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for Stream and Spring Cloud integration.
- Upstream/downstream versions and cross-service boundaries.
- Differences across the eight maintenance lines.

### ⚠️ Needs Input

- Target Cloud line, Boot parent, and POM.
- Capabilities, external services, and deployment requirements.
- Current source/test/remote evidence.

### ❌ Out of Scope

- Treating README module names as completed capabilities.
- Substituting configuration presence for external service behavior.
- Unauthorized releases or production operations.

## Workflow

### Step 1: Confirm the source of truth

Run `ddd4j-cloud-version-selection` to fix the combination, then locate the stream extension, `BindingNamingContributor`, and the broker integration tests on the confirmed branch and SHA.

### Step 2: Define bindings

Map functions, binding names, and physical destinations per broker. Confirm binder names and destination rules against `BindingNamingContributor`, and do not assume cross-broker uniformity.

### Step 3: Wire reliability

Configure `StreamBridge` publishes and consumer ACK/NACK with retry and dead-letter policy, and propagate Context/Tenant into message headers with restoration on consume.

### Step 4: Test against real brokers

Run broker integration tests (Kafka, RabbitMQ, Pulsar, RocketMQ as applicable): publish/consume, ack/nack/retry, duplicates, and recovery. Mark external-service gaps NOT VERIFIED or BLOCKED(upstream) where applicable.

### Step 5: Report the binding map

Output the binding map (function → binding → destination → broker) with configuration keys, reliability settings with lifecycle owners, tests executed with evidence per tier, and risks with proposed fixes.

## Gotchas

- Spring Cloud Stream has three distinct names — the function name, the binding name, and the physical destination — and confusing them is the most common misconfiguration; the app can start healthy while producing to the wrong place.
- ACK mode differs per binder: Kafka and RabbitMQ do not share defaults, so an acknowledgment policy copied between brokers changes delivery semantics silently.
- A binder on the classpath does not mean the broker is reachable — startup can succeed with the broker down, and the failure only surfaces at first publish or consume.
- Renaming a binding through `BindingNamingContributor` rules can point the flow at a new physical destination and orphan the messages sitting in the old one.
- Retry without a dead-letter policy turns a poison message into infinite redelivery or silent loss, depending on the binder.
- Message headers do not carry Context/Tenant automatically — the producer must write them and the consumer must restore them onto the binder thread, or downstream processing runs without tenant isolation.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；消息与 Broker 地址示例均为脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-cloud-stream` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-stream` to review existing usage against the current source."
- "Use `$ddd4j-cloud-stream` to return an implementation choice, evidence state, and remaining risk."

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
