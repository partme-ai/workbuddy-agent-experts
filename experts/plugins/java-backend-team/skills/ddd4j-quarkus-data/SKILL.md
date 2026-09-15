---
name: ddd4j-quarkus-data
description: Use when integrating Panache, JPA, JDBI, R2DBC, repositories, composite keys, tenants, transactions, EventStore, Projection, or Outbox with ddd4j-quarkus. 中文触发词：数据访问集成、Panache、JPA、JDBI、R2DBC、租户隔离、事务边界、EventStore、Outbox。
license: Apache-2.0
---

# ddd4j-quarkus Data

## Overview

Covers Panache, JPA, JDBI, R2DBC, Repository, composite keys, tenants, transactions, EventStore, Projection, and Outbox uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Choosing among Panache, JPA, JDBI, and R2DBC for a ddd4j-quarkus service and wiring the `Repository` SPI.
- Defining composite keys, tenant isolation, and transaction boundaries for Quarkus data access.
- Implementing EventStore, Projection, or Outbox behavior on Quarkus with real transactional guarantees.
- Owning datasource lifecycle: startup/shutdown observers and idempotent close.
- Confirming reflection/serialization registrations for entity classes under native image.
- Testing against real databases with QuarkusTest — transactions, rollback, EventStore round-trips, startup failure.

## When NOT to Use

Do not use this skill when:

- **Spring Boot data access (MyBatis, MyBatis-Plus, Flyway)** — use `ddd4j-boot-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-data`; do not use this skill to port Boot mappers to Quarkus piecemeal.
- **Javalin data access** — use `ddd4j-javalin-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-data`.
- **The `Repository`/`Query` SPI contracts themselves are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Caching query results or idempotency keys** — use `ddd4j-quarkus-cache` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-cache`.
- **Build-time internals of a data extension (BuildItems, Recorders)** — use `ddd4j-quarkus-extension-authoring` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-extension-authoring`.
- **The project is plain Quarkus + Hibernate without ddd4j** — generic Quarkus/Hibernate guidance applies; do not use the ddd4j Repository SPI model on a non-ddd4j stack.

## Trigger Keywords

**English**: data access integration, Panache, JPA, JDBI, R2DBC, tenant isolation, transaction boundary, EventStore, Outbox, composite key

**中文**: 数据访问集成, Panache, JPA, JDBI, R2DBC, 租户隔离, 事务边界, EventStore, Outbox, 复合主键

## Core Scope

Panache, JPA, JDBI, R2DBC, Repository, composite keys, tenants, transactions, EventStore, Projection, Outbox.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for data access and Quarkus adaptation.
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

Fix the line via `ddd4j-quarkus-version-selection`, then locate `ddd4j-quarkus-data` and the Quarkus/Panache adapters in that checkout. The supported access stacks are per line.

### Step 2: Select the access stack

Choose Panache, JPA, JDBI, or R2DBC against the consistency and reactive requirements, confirm `Repository` wiring, and define composite keys, tenant isolation, and transaction boundaries up front.

### Step 3: Verify lifecycle and native support

Confirm datasource owners, startup/shutdown observers, and idempotent close, plus the reflection/serialization registrations needed for native image.

### Step 4: Test against real databases

Run QuarkusTest suites against real databases covering transactions, EventStore, Projection, and Outbox behavior, including startup failure and rollback paths — an H2-only suite does not prove production behavior.

### Step 5: Report

Produce a single report: chosen stack with configuration keys, lifecycle owners and native registrations, tests executed and evidence state per tier, and risks with proposed fixes and missing inputs.

## Gotchas

- `quarkus.hibernate-orm`-style configuration is build-time fixed: some properties cannot be changed at runtime, and a `%prod.runtime` override for them silently does nothing or fails the build.
- Panache active-record patterns must not leak into the ddd4j domain — the domain depends on the `Repository` SPI; entities stay in the data adapter.
- EventStore persistence and snapshot `save()` on the same aggregate mix persistence tracks; the Outbox writes what `pullDomainEvents()` produced, nothing else.
- Native image requires explicit registration for entity classes reached reflectively; JVM-mode data tests pass while the native build fails on the first mapped entity.
- Testcontainers suites need Docker, and Docker detection is special across Quarkus's classloaders — an unavailable Docker run is BLOCKED/SKIPPED, never PASS.
- Datasource close must be idempotent and owned by a shutdown observer; closing twice during shutdown (observer plus framework) masks the real shutdown error.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；数据源配置示例仅使用脱敏占位符。

## Quick Start

- "Use `$ddd4j-quarkus-data` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-data` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-data` to return an implementation choice, evidence state, and remaining risk."

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
