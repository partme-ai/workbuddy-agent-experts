---
name: ddd4j-boot-data
description: Use when integrating ddd4j data capabilities in Spring Boot with JDBC, JPA, MyBatis, MyBatis-Plus, database migrations, transactions, repositories, projections, or Outbox. 中文触发词：数据访问、MyBatis、MyBatis-Plus、JPA、事务、数据库迁移、Projection、Outbox。
license: Apache-2.0
---

# ddd4j-boot Data

## Overview

Covers JDBC, JPA, MyBatis, MyBatis-Plus, Flyway, transactions, Repository, Projection, and Outbox uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Choosing among JDBC, JPA, MyBatis, and MyBatis-Plus for a ddd4j-boot service and assembling it through the boot data auto-configuration.
- Registering the concrete `Repository` implementation that the domain's `Repository` SPI expects.
- Wiring transactions and the transaction manager around aggregate persistence, Projections, and the Outbox.
- Setting up Flyway migrations, including verifying up/down against a real database.
- Overriding data defaults with user beans, or checking why an assembled data bean is not the implementation you expected.
- Diagnosing data-access failures on a specific Boot line (2.3–4.1): wiring present but round-trips failing, transactions not rolling back, Outbox not dispatching.

## When NOT to Use

Do not use this skill when:

- **The `Repository` / `Query` SPI contracts themselves need changing** — use `ddd4j-data` (adapter-level SPIs) or `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-data`.
- **The domain model is deciding which access style fits it** — use `ddd4j-core` for the aggregate/repository contracts; this skill should not reshape the domain around an ORM.
- **Generic auto-configuration mechanics are the question, not data** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The runtime is Javalin, Quarkus, or Spring Cloud** — use the matching `ddd4j-javalin-data`, `ddd4j-quarkus-data`, or `ddd4j-cloud-data` skill instead; the Boot assembly does not transfer.
- **The project is plain Spring Boot without ddd4j** — generic Spring Data JPA / MyBatis skills apply.
- **The test doubles and database fixtures for verification are the question** — use `ddd4j-boot-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-testing`.

## Trigger Keywords

**English**: data access, MyBatis, MyBatis-Plus, JPA, transactions, database migration, Projection, Outbox

**中文**: 数据访问, MyBatis, MyBatis-Plus, JPA, 事务, 数据库迁移, Projection, Outbox
## Core Scope

JDBC, JPA, MyBatis, MyBatis-Plus, Flyway, transactions, Repository, Projection, Outbox.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among data implementations and Spring Boot assembly.
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

Run `ddd4j-boot-version-selection` to fix the line, then locate the data AutoConfiguration, its Properties, and the corresponding `ddd4j-data` modules on that line.

### Step 2: Select the access implementation

Compare JDBC, JPA, MyBatis, and MyBatis-Plus against the project's data model and existing investment. Confirm the Flyway wiring and which transaction manager the assembly registers.

### Step 3: Verify the wiring

Check conditional wiring, default beans, and user bean override points. Confirm the off switch truly skips assembly, and that every resource (data source, transaction manager, executor) has an explicit owner with rollback on failure and idempotent close.

### Step 4: Test against a real database

Execute context tests plus real database round-trips, transaction commit/rollback behavior, Projection reads, and Outbox dispatch. Cover migration up/down against a real database where possible — an H2 unit test does not prove production dialect behavior.

### Step 5: Report with separated evidence

Report the chosen implementations with configuration keys, the AutoConfiguration entry and override points, test results, and evidence state — configuration presence, bean creation, behavior, CI, and publish reported separately — plus risks and missing inputs.

## Gotchas

- A JDBC driver and a data module on the classpath do not prove the assembled `Repository` implementation is the one the domain expects — two data starters can each satisfy the same SPI with different beans.
- A `destroyMethod` that never runs leaks connection pools on context close; the leak shows up in long test suites and restarts, not in a single green run.
- An H2 unit test does not prove production dialect behavior — migrations and SQL that pass on H2 can fail on MySQL/PostgreSQL the first time they run for real.
- Bean creation is not database availability: a started context proves wiring, not that Flyway ran or that transactions actually roll back.
- Flyway up-migrations passing says nothing about down-migrations; verify both before trusting the lifecycle.
- Copying data wiring across Boot lines breaks on API changes (Boot 2.3–4.1 span very different transaction and datasource APIs); each line adapts individually.
- Printing datasource configuration for troubleshooting can leak credentials — sensitive values must be redacted.

## Output and Exceptions

When information is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output credentials, tokens, production connection strings, or sensitive business data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例数据均为脱敏的虚构记录。

## Quick Start

- "Use `$ddd4j-boot-data` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-data` to review existing usage against the current source."
- "Use `$ddd4j-boot-data` to return an implementation choice, evidence state, and remaining risk."

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
