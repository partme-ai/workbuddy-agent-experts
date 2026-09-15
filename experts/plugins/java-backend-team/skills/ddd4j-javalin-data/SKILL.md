---
name: ddd4j-javalin-data
description: Use when integrating MyBatis, JPA, PostgreSQL, repositories, transactions, EntityManagerFactory, EventStore, Projection, or Outbox with ddd4j-javalin. 中文触发词：MyBatis、JPA、PostgreSQL、Repository、事务、EventStore、Outbox、数据源集成。
license: Apache-2.0
---

# ddd4j-javalin Data

## Overview

Covers MyBatis, JPA/PostgreSQL, Repository, transactions, EMF, EventStore, Projection, and Outbox uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Wiring MyBatis or JPA/PostgreSQL repositories, transactions, and the `Repository` SPI into a ddd4j-javalin service on 6.7.x, 7.1.x, or 7.2.x.
- Assigning lifecycle ownership for the JPA `EntityManagerFactory`, EventStore, Projection, and Outbox, including initialization order and reverse-order rollback on partial startup failure.
- Contributing real database availability to aggregated readiness, and wiring drain plus idempotent close for data resources.
- Running real database round-trip tests: transactions, conflicts, Projection advancement, and Outbox delivery.

## When NOT to Use

Do not use this skill when:

- **The aggregate model, `Repository` SPI signature, or event contracts are being designed** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Outbox message transport is the question (MQ consumers, publishers, ack/retry)** — use `ddd4j-javalin-mq` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-mq`.
- **Route-level payload validation or error responses are the question** — use `ddd4j-javalin-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-web`; for lifecycle participant mechanics use `ddd4j-javalin-runtime`.
- **A cross-capability review or release gate is needed** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **Spring Boot, Quarkus, or Spring Cloud data wiring is the question** — use `ddd4j-boot-data`, `ddd4j-quarkus-data`, or `ddd4j-cloud-data` instead, for example Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-data`.
- **The project is generic JPA/MyBatis without ddd4j** — do not use this skill; use `java-skills` instead, since the ddd4j `Repository`/`EventStore` contracts do not exist there.

## Trigger Keywords

**English**: MyBatis, JPA, PostgreSQL, repository, transactions, EventStore, Outbox, EntityManagerFactory

**中文**: MyBatis, JPA, PostgreSQL, Repository, 事务, EventStore, Outbox, 数据源集成

## Core Scope

MyBatis, JPA/PostgreSQL, Repository, transactions, EMF, EventStore, Projection, Outbox.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for data access and Javalin adaptation.
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

Fix the maintenance line with `ddd4j-javalin-version-selection`, then locate the data module, its `EntityManagerFactory` wiring, and the database tests in the current checkout.

### Step 2: Select the access stack

Choose MyBatis or JPA/PostgreSQL and confirm the `Repository` implementations and transaction boundaries. Confirm the initialization order of EventStore, Projection, and Outbox against the aggregate lifecycle.

### Step 3: Manage the data lifecycle

Confirm the `EntityManagerFactory`, schedulers, and listeners each have exactly one owner registered as a lifecycle participant. Verify drain, idempotent close, and that the database contributes to aggregated readiness.

### Step 4: Test with a real database

Run real database round-trips — transactions, conflicts, Projection advancement, Outbox delivery — plus startup failure and rollback behavior. In-memory substitutes and skipped containers must be reported as `BLOCKED`/`SKIPPED`, not green.

### Step 5: Report the data state

Produce a single report: chosen stack with configuration keys and connection handling, lifecycle owners and shutdown order, tests executed with evidence state per tier, and risks with proposed fixes and missing inputs.

## Gotchas

- The JPA `EntityManagerFactory` must have exactly one lifecycle owner — two owners close it twice, zero owners leak it across embedded-test restarts.
- A `Repository` method existing on the interface is not behavior: an unoverridden default method surfaces as `UnsupportedOperationException` from the registered adapter at first use.
- Outbox delivery and the business transaction are separate concerns — a DB commit never proves the event was delivered, and an MQ ack never proves the row committed.
- Readiness must reflect real database availability; a hardcoded READY converts a DB outage into request storms instead of load-shedding.
- EMF/EventStore/Projection/Outbox initialization order decides rollback on partial failure — a later participant failing must close the earlier ones in reverse order.
- The maintenance lines do not change MyBatis/JPA semantics, but the per-line JDK contract does — 7.2.x-only Java syntax must not leak into the 6.7.x/7.1.x baselines.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；数据库示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-data` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-data` to review existing usage against the current source."
- "Use `$ddd4j-javalin-data` to return an implementation choice, evidence state, and remaining risk."

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
