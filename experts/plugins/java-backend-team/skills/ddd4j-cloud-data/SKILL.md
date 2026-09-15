---
name: ddd4j-cloud-data
description: Use when integrating ddd4j-cloud data sources, MyBatis, JPA, transactions, Seata, tenants, migrations, repositories, or database-specific behavior. 中文触发词：数据源、事务、分布式事务、Seata、数据迁移、租户过滤、仓储。
license: Apache-2.0
---

# ddd4j-cloud Data

## Overview

Covers datasource, MyBatis, JPA, transactions, Seata, tenant, migration, and repository uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Selecting the access stack (datasource, MyBatis, JPA) for a ddd4j-cloud service and wiring repositories.
- Choosing between local transactions and Seata for cross-service work.
- Planning migration execution order and tenant-aware migration filtering.
- Wiring datasource lifecycle: owner, failure rollback, idempotent close.
- Verifying real database round-trips — transactions, tenant isolation, migration up/down.
- Diagnosing data-access failures that only appear with the real database in the loop.

## When NOT to Use

Do not use this skill when:

- **Tenant isolation rules are the question** (ignore rules, exempt tables, data-scope semantics) — use `ddd4j-cloud-tenant` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-tenant`.
- **The `Repository` SPI contract in the domain is the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-data`.
- **The runtime is Javalin or Quarkus** — use `ddd4j-javalin-data` or `ddd4j-quarkus-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-data` (or `--skill ddd4j-quarkus-data`).
- **Messaging and brokers are the question** — do not use this skill; brokers are not databases. Use `ddd4j-cloud-stream` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-stream`.
- **Generic Spring Data JPA / MyBatis integration without ddd4j** — apply generic `spring-data-jpa` / Java guidance instead (no install command).

## Trigger Keywords

**English**: datasource, transaction, distributed transaction, Seata, migration, tenant filtering, repository wiring

**中文**: 数据源, 事务, 分布式事务, Seata, 数据迁移, 租户过滤

## Core Scope

Datasource, MyBatis, JPA, transaction, Seata, tenant, migration, repository.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for data access and Spring Cloud integration.
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

Run `ddd4j-cloud-version-selection` to fix the combination, then locate the cloud data extensions and database tests on the confirmed branch and SHA.

### Step 2: Select the access stack

Choose datasource, MyBatis, or JPA and confirm repository wiring against the line's extensions. Decide the transaction strategy — local or Seata — with tenant-aware isolation stated explicitly.

### Step 3: Wire migrations and lifecycle

Confirm migration execution order and tenant-aware filtering, and confirm datasource owners, failure rollback, and idempotent close.

### Step 4: Test against the real database

Run real database round-trips: transactions, tenant isolation, migration up/down. Cover cross-service transactions wherever Seata is used.

### Step 5: Report the data layer

Output the chosen stack with configuration keys, the transaction and tenant strategy with owners, tests executed with evidence per tier (marking NOT VERIFIED where external behavior lacks proof), and risks with proposed fixes.

## Gotchas

- A datasource or Seata coordinator configured in YAML is not evidence of connectivity — startup can succeed while the database or the Seata transaction coordinator is down, and cross-service rollback silently degrades.
- Migration ordering interacts with tenant filtering: a migration that adds the tenant column must run before filtering activates on that table, or bootstrapping breaks.
- The compatibility pairing for these lines is WebMVC/MySQL — a green H2 or in-memory suite does not prove MySQL behavior.
- Tenant-aware filtering lives at the data layer and is only as strong as its weakest access path; any client that bypasses the repository skips it (rules belong to `ddd4j-cloud-tenant`).
- A `Repository` default method may throw `UnsupportedOperationException` when the data adapter does not override it — interface presence is not behavior.
- A transaction does not follow a thread hop: work continued in `@Async` or after a Feign call is outside the original transaction unless propagation is arranged explicitly (Seata or local).

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；连接串与数据表示例均为脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-cloud-data` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-data` to review existing usage against the current source."
- "Use `$ddd4j-cloud-data` to return an implementation choice, evidence state, and remaining risk."

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
