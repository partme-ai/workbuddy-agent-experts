---
name: ddd4j-data
description: Use when choosing, implementing, or reviewing ddd4j persistence with JDBC, JDBI, JPA, MyBatis, MyBatis-Plus, R2DBC, Panache, EventStore, Projection, Outbox, transactions, tenants, or Domain-to-PO mapping. 中文触发词：持久化选型、EventStore、Projection、Outbox、事务边界、租户隔离、领域对象映射、乐观并发。
license: Apache-2.0
---

# ddd4j Data

## Overview

Pick the persistence model first, then the technology. Snapshot Repository, Event Sourcing, Projection, and Outbox are distinct responsibilities that may be combined but must not blur transaction boundaries.

## When to Use

- Choosing the persistence technology: JDBC, JDBI, JPA, MyBatis/MyBatis-Plus, R2DBC, Panache, or ESDB EventStore.
- Mapping between `AggregateRoot` and PO/Entity classes, and wiring `Query<M>` persistence scopes.
- Implementing the `EventStore` / `AsyncEventStore` port with expected-version checks and atomic batch appends.
- Building read models with `ProjectionRunner` / `ProjectionService` and `ProjectionPositionRepository`.
- Implementing the Transactional Outbox with claim / send / confirm semantics.
- Defining transaction boundaries, tenant scoping, encrypted fields, and auditing at the persistence layer.

## When NOT to Use

Do not use this skill when:

- **The aggregate or domain model itself must be designed** (Active Record vs Event Sourcing semantics, event handlers) — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **ORM field metadata is the question** (`@BizKey`, `@TenantId`, `@OnCreate` consumers) — use `ddd4j-annotation` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-annotation`.
- **Reliable event delivery to a broker after commit is the question** — use `ddd4j-mq` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-mq` (this skill owns the Outbox write side only).
- **Generic MyBatis-Plus or JPA usage with no ddd4j contracts involved** — use the framework's own skills; do not map ddd4j port names onto an unrelated persistence setup.
- **An H2 unit test is being offered as production database proof** — do not use this skill to bless that; dialect, transaction, and concurrency claims require a real database.

## Trigger Keywords

**English**: persistence selection, EventStore, Projection, Outbox, transaction boundary, tenant isolation, Domain PO mapping, optimistic version

**中文**: 持久化选型, EventStore, Projection, Outbox, 事务边界, 租户隔离, 领域对象映射, 乐观并发

## Technology Selection

| Capability | Implementation |
|---|---|
| Synchronous SQL | JDBC, JDBI |
| ORM | JPA |
| Mapper | MyBatis, MyBatis-Plus |
| Reactive | R2DBC |
| Quarkus ORM | Panache |
| Event storage | JDBI / JPA / R2DBC / Panache / ESDB EventStore |
| Read model | Projection + multi-runtime scheduler / repository |
| Reliable publish | Transactional Outbox |

## Core Rules

1. Keep Domain `AggregateRoot` separate from PO / Entity.
2. The `Repository` port lives in core; the implementation lives in data.
3. `Query` binds to the domain model; PO fields are mapped through a persistence scope or metadata.
4. EventStore append must validate the expected version and batch atomicity.
5. Projection position updates and read-model writes need an explicit transaction and idempotency.
6. The Outbox must share a transaction with the business write, then claim / send / confirm independently.
7. Real-database tests prove dialect, transaction, concurrency, and visibility behavior.

## Capability Boundaries

### ✅ Strong At

- Technology selection and Domain / PO mapping.
- Repository, EventStore, Projection, Outbox.
- Tenant, data scope, and encrypted fields.
- Synchronous and reactive transaction boundaries.

### ⚠️ Needs Input

- Database, runtime, and maintenance line.
- Aggregate, PO, Query, and ID.
- Consistency and concurrency requirements.

### ❌ Out of Scope

- Treating an H2 unit test as production database proof.
- Defaulting to in-memory filtering on production-sized data.
- Using focused tests to claim transaction or concurrency coverage.

## Workflow

### Step 1: Choose snapshot or event sourcing

Decide the persistence model per aggregate: snapshot Repository (`save`/`load`) or Event Store append with `loadFromHistory`. Record the choice; never mix tracks on one aggregate.

### Step 2: Define the Aggregate / PO / Query mapping

Keep `AggregateRoot` free of persistence annotations; map to PO explicitly, and bind `Query<M>` to the domain model with PO fields exposed only through an explicit persistence scope or metadata.

### Step 3: Choose the technology

Select JDBC/JDBI for synchronous SQL, JPA or MyBatis/MyBatis-Plus for ORM/mapper styles, R2DBC or Panache for reactive/Quarkus, and one of the JDBI/JPA/R2DBC/Panache/EventStoreDB implementations for the `EventStore` port.

### Step 4: Define transactions, tenants, encryption, and auditing

Fix the transaction boundary per use case, add tenant scoping to keys and queries, mark encrypted fields, and wire audit population — each through the adapter, never through the domain.

### Step 5: Add Projection or Outbox when needed

For read models, pair `ProjectionRunner`/`ProjectionService` with `ProjectionPositionRepository` under explicit transactions. For reliable publishing, share one transaction among business write, event, and Outbox row, then claim/send/confirm independently.

### Step 6: Run real-database tests

Cover dialect behavior, rollback, concurrency (`AggregateVersionConflictException`), ordering, and crash recovery against a real database container — an H2 unit test is not production proof.

## Gotchas

- `AggregateRoot` doubling as the framework PO because "it's faster" — the aggregate then carries persistence annotations into the domain, and every framework upgrade leaks into business logic.
- Raw MyBatis in-memory filtering reaching production — a `Wrapper` that paginates in memory after loading the full table passes every small test set and times out on the first real dataset.
- EventStore append and the business write committing in separate transactions — a crash between them yields an aggregate with no events, or events with no aggregate, and no test fails until the first real failure.
- `MAX(position)+1` position allocation — two concurrent projections read the same MAX and collide; the allocator must be atomic (unique constraint with retry or an atomic allocator).
- Projection advancing `ProjectionPositionRepository` before the read-model write commits — a crash in between permanently skips that event in the read model.
- Outbox rows marked "sent" on send and re-sent after a crash before confirm — without idempotent consumption keyed on event/message id, the duplicate is delivered twice.
- Declaring database proof from an H2 suite — H2 agrees with your dialect assumptions by accident; real-database tests exist because H2 does not emulate locking, concurrency, or visibility behavior.

## Deep Reference

- [Storage Selection](references/storage-selection.md)
- [MyBatis](references/mybatis.md)
- [EventStore](references/event-store.md)
- [Projection](references/projection.md)
- [Outbox and Transactions](references/outbox-and-transactions.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Test data must be masked. SQL, event, and Outbox logs must not expose credentials or private payloads. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；SQL、事件与 Outbox 示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-data` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-data` to review existing usage against the current source."
- "Use `$ddd4j-data` to return an implementation choice, evidence state, and remaining risk."

## Audience and Customization

- Developers: provide the target maintenance line, POM, capabilities, and acceptance behavior.
- Architects: specify a read-only boundary, compatibility, or migration review.
- Testers / release engineers: specify the required evidence levels; do not auto-expand to release or production operations.

Customize the target framework, allowed implementations, excluded modules, compatibility requirements, and evidence level. When input is insufficient, give a tentative verdict first, then list `missing: specific item; how to provide: path or configuration`.

## FAQ

1. **Are skills organized by Maven artifact?** No — by the user-facing capability domain.
2. **Can I copy another maintenance line directly?** No — verify the version and source first.
3. **Does a class existing in source prove the capability works?** No — registration and behavior evidence are also required.
4. **How do I report tests that did not run?** Mark `NOT RUN` or `BLOCKED`.
5. **Can the skill commit or release automatically?** Only after explicit user authorization.
6. **What if the implementation is missing?** Describe the missing module or evidence; do not invent APIs.
