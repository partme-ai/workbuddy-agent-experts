---
name: ddd4j-cloud-testing
description: Use when testing ddd4j-cloud compatibility, Web MVC and MySQL, context propagation, Feign, Spring Cloud Stream binders, databases, brokers, or remote consumers. 中文触发词：兼容测试、集成测试、维护矩阵、远端消费者、证据分级、测试报告。
license: Apache-2.0
---

# ddd4j-cloud Testing

## Overview

Covers compatibility, WebMVC/MySQL, Context, Feign, Binder, DB, Broker, and remote consumers uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Planning the compatibility suite for a line, including the WebMVC/MySQL pairing.
- Designing context propagation, Feign round-trip, and binder tests against real databases and brokers.
- Running container-based suites where Docker exists and remote-consumer verification against the private repository.
- Recording evidence honestly: NOT VERIFIED, BLOCKED(upstream), BLOCKED(infrastructure).
- Auditing a test report for hidden skips, embedded-only coverage, or misclassified failures.
- Deciding what evidence tier a release gate still lacks.

## When NOT to Use

Do not use this skill when:

- **Implementing the capability under test is the question** — use the matching `ddd4j-cloud-*` capability skill instead (context, feign, stream, data, web, tenant, observability).
- **Publishing artifacts or proving remote consumption after a release is the goal** — use `ddd4j-cloud-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-release` (testing stops at evidence; it does not publish).
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-testing`.
- **The runtime is Javalin or Quarkus** — use `ddd4j-javalin-testing` or `ddd4j-quarkus-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-testing` (or `--skill ddd4j-quarkus-testing`).
- **Core contract tests for aggregates, events, or replay are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Generic JUnit/Testcontainers practice without ddd4j** — do not use this skill; apply generic Java testing guidance instead (no install command).

## Trigger Keywords

**English**: compatibility testing, integration suite, WebMVC MySQL pairing, remote consumer, evidence grading, test report, skipped tests

**中文**: 兼容测试, 集成测试, 维护矩阵, 远端消费者, 证据分级, 测试报告

## Core Scope

Compatibility, WebMVC/MySQL, Context, Feign, Binder, DB, Broker, remote consumer.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for testing and Spring Cloud integration.
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

Run `ddd4j-cloud-version-selection` to fix the combination, then locate the compatibility tests, src/test suites, and verification consumers on the confirmed branch and SHA.

### Step 2: Design the suite

Plan compatibility tests for the WebMVC/MySQL pairing, plus context propagation, Feign round-trips, and binder tests against real databases and brokers.

### Step 3: Execute the suite

Run the unit/behavior suites and the container-based suites where Docker exists, then run remote-consumer verification against the private repository.

### Step 4: Record evidence honestly

Classify external-service gaps as NOT VERIFIED, upstream gaps as BLOCKED(upstream), and non-started CI as BLOCKED(infrastructure). Never translate skips into success.

### Step 5: Report the evidence

Output the suites executed with the combination and toolchain, pass/fail plus the BLOCKED/SKIPPED/NOT VERIFIED inventory, gaps against the feature matrix, and risks with proposed fixes.

## Gotchas

- Never translate skips into success — a green report with unexamined SKIPPED entries is the single most common false evidence in this pipeline.
- The three failure classes are not interchangeable: external service unreachable is NOT VERIFIED, missing upstream artifact is BLOCKED(upstream), CI that never started is BLOCKED(infrastructure) — conflating them hides the real blocker.
- The compatibility pairing is WebMVC/MySQL specifically: an H2 or embedded-suite pass does not satisfy the pairing and must not be reported as compatibility evidence.
- Mocked context and tenant fixtures prove wiring shape only — ThreadLocal-based context does not cross `@Async`, Reactor, or Feign boundaries in the real runtime, so propagation claims need real round-trips.
- Embedded or in-memory brokers do not share ACK/retry defaults with real Kafka/RabbitMQ — binder evidence only counts from the real broker.
- When Docker is absent, container suites must be recorded as skipped with the reason, not silently omitted from the report.
- Remote-consumer verification requires isolated clean-cache consumption (`-U`); a warm local repository hides exactly the metadata gaps the check exists to find.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；测试报告示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-cloud-testing` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-testing` to review existing usage against the current source."
- "Use `$ddd4j-cloud-testing` to return an implementation choice, evidence state, and remaining risk."

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
