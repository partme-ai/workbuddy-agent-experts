---
name: ddd4j-core
description: Use when implementing or reviewing current ddd4j domain models, aggregate roots, CQRS commands/queries, domain events, repository SPI, context, subject, cache, or health contracts; not for legacy io.hiwepy.boot CRUD conventions. 中文触发词：聚合根、领域事件、命令总线、仓储接口、上下文清理、事件溯源。
license: Apache-2.0
---

# ddd4j Core

## Overview

Guide domain modeling and framework-agnostic code against the current `io.ddd4j.core` public contracts. The core boundary is: `ddd4j-core` defines DDD / CQRS / SPI; Spring, Guice, Quarkus, Javalin, MyBatis, and friends only assemble in the adapter layer.

## When to Use

- Modeling or reviewing a ddd4j domain aggregate (`AggregateRoot<ID>`) in Active Record or Event Sourcing mode.
- Implementing the write side — `Command`, `CommandExecutor`, `CommandBus`, `Result<R>`.
- Implementing the read side — `Query<M>`, `PersistenceQueryScope<M, P>`, `Repository<M, ID>`.
- Working with `DomainEvent<ID>` metadata, publication, or replay.
- Deciding whether a dependency belongs in the domain or in the adapter layer.
- Resolving `Contexts`, `ThreadContext`, `Subject`, or `Cache` SPI contracts.

## When NOT to Use

Do not use this skill when:

- **Module boundaries or dependency direction are the question** — use `ddd4j-architecture` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-architecture`.
- **Annotation retention, targets, or consumers are the question** — use `ddd4j-annotation` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-annotation`.
- **Maven parent, BOM, or version ownership is the question** — use `ddd4j-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-bom`.
- **JSON, bean, string, collection, or ID utilities are the question** — use `ddd4j-kit` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-kit`.
- **A concrete ORM, broker, or cache product must be configured** — use `ddd4j-data`, `ddd4j-mq`, or `ddd4j-cache`.
- **The project is not on ddd4j** — generic DDD and Java skills apply; do not retrofit ddd4j types onto a non-ddd4j codebase.
- **The code still uses `io.hiwepy.boot` CRUD base classes** — that is a legacy contract, not the current `ddd4j-core` API.

## Trigger Keywords

**English**: aggregate root, domain event, CQRS command, query, repository SPI, event sourcing, context cleanup, subject

**中文**: 聚合根, 领域事件, 命令总线, 查询, 仓储接口, 事件溯源, 上下文清理, 主题

## Quick Start

- "Build an event-sourced aggregate with ddd4j."
- "Implement Command, CommandExecutor, and the CommandBus dispatch."
- "Review whether the domain layer wrongly depends on Spring or MyBatis."
- "Explain the boundary between `ThreadContext`, `Contexts`, and `Subject`."

## Audience, Routing, and Customization

- **Domain developers** — provide the aggregate strategy, target maintenance line, and business invariants.
- **Adapter developers** — provide the runtime, repository / bus implementation, and transaction boundaries.
- **Reviewers** — require read-only inspection and specify whether the focus is DDD, CQRS, context, or SPI.
- **Non-ddd4j projects** — hand off to the generic DDD / Java skills; do not retrofit ddd4j types.

When input is insufficient, give a tentative verdict based on the current checkout first, then list `missing: specific item; how to provide: path, branch, or contract`.

Always confirm the current branch first; the 1.0.x, 2.0.x, and 3.0.x APIs are not interchangeable by name.

## Capability Boundaries

### ✅ Strong At

1. `AggregateRoot<ID>` with both Active Record and Event Sourcing modes.
2. `Command`, `CommandExecutor`, `CommandBus`, and `Result<R>` write-side contracts.
3. `Query<M>`, `PersistenceQueryScope<M, P>`, and `Repository<M, ID>`.
4. `DomainEvent<ID>` metadata, publication, replay, and event handlers.
5. `Contexts` / `ThreadContext`, `Subject`, `Cache`, and other framework-agnostic SPIs.

### ⚠️ Needs Input

1. Target maintenance line with source code and POM.
2. Domain model, persistence strategy, and transaction boundary.
3. Runtime adapter and real acceptance behavior.

### ❌ Out of Scope

1. `io.hiwepy.boot.api.*` — `BaseEntity`, `PaginationEntity`, `ApiRestResponse`.
2. Treating Spring annotation semantics as the universal runtime contract.
3. Replacing specific MyBatis / JPA / Jackson / Sa-Token adapter skills.

## Core Rules

| Topic | Current Contract |
|---|---|
| Aggregate root | Extend `AggregateRoot<ID>`; the identifier implements `Serializable` |
| Persistence mode | Choose Active Record OR Event Sourcing — never mix both on the same aggregate |
| Events | Subclasses keep a no-arg constructor; use `registerEvent`, replay via `loadFromHistory` |
| Commands | `Command` expresses intent; executed by `CommandExecutor`, dispatched via `CommandBus.execute` |
| Queries | `Query<M>` binds to the domain model; opt into PO fields with explicit `persistence(P.class)` |
| Repository | Domain only depends on `Repository`; the implementation is registered by the data / runtime adapter |
| Context | Request / thread scopes must be released on completion — Subject or tenant data must not leak |
| Cache | Domain depends only on the `Cache` SPI; cross-instance atomic semantics must be proven by the implementation |

## Examples

```java
public final class Order extends AggregateRoot<OrderId> {
    private OrderStatus status;

    public void pay() {
        if (status == OrderStatus.PAID) {
            throw new IllegalStateException("Order already paid");
        }
        registerEvent(new OrderPaid(id()));
    }

    @EventHandler
    void apply(OrderPaid event) {
        status = OrderStatus.PAID;
    }
}
```

When using event sourcing, persist `pullDomainEvents()` and stop calling snapshot-style `save()` / `update()`.

## Workflow

### Step 1: Confirm the maintenance line

Identify the current branch (`1.0.x`, `2.0.x`, or `3.0.x`) and read the active `AggregateRoot`, `Command`, `Query`, `Repository`, and `DomainEvent` source. The three lines are not interchangeable by name.

### Step 2: Choose the persistence mode

Decide Active Record (snapshot `save()`) or Event Sourcing (`pullDomainEvents()` plus `loadFromHistory`). Decide once per aggregate and record the choice; never mix both on the same aggregate.

### Step 3: Model the aggregate

Extend `AggregateRoot<ID>`, keep all mutations inside the aggregate body, register events with `registerEvent(...)`, apply them in `@EventHandler` methods, and preserve a no-arg constructor on every event subclass.

### Step 4: Wire the contracts

Define `Command` / `CommandExecutor` for the write path and `Query<M>` for the read path. The domain depends only on the `Repository` SPI; concrete data adapters register the implementations.

### Step 5: Verify behavior

Run aggregate invariant tests, event replay tests, command result tests, and context cleanup tests. Confirm the domain layer compiles without framework imports.

## Gotchas

- Continuing the legacy `BaseEntity / Model<T>` inheritance chain — the current contract is `AggregateRoot<ID>`.
- Importing Spring or MyBatis Wrapper types directly into the core domain layer.
- Persisting both aggregate snapshots and uncommitted events on the same aggregate.
- Treating `DomainEvent.source()` as a complete `EntityIdPath` — it is a string-compatible view only.
- Assuming `Repository` default methods work without testing the actual adapter; they may throw `UnsupportedOperationException`.
- Binding `ThreadContext` but failing to clean it up in a `finally` block or scope close, leaking Subject or tenant data.
- Copying `3.0.x` Java, Jackson, or API semantics directly onto older lines without re-verification.

## Output and Exceptions

Cite specific package names, source paths, and maintenance lines. When a symbol cannot be resolved, return `missing: symbol or module in the current branch; how to provide: confirm branch, POM, and source path`. Do not substitute legacy project types.

## Capability Routing

- Module boundaries and dependency direction — hand off to **`ddd4j-architecture`**. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-architecture`.
- Annotation semantics and consumers — hand off to **`ddd4j-annotation`**. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-annotation`.
- Maven / BOM / version ownership — hand off to **`ddd4j-bom`**. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-bom`.
- JSON, Bean, string, collection, and ID utilities — hand off to **`ddd4j-kit`**. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-kit`.

## Privacy and Security

Examples use fictitious orders and identifiers. Never output real tokens, tenant data, user profiles, or private-repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例仅使用脱敏的虚构数据。

## FAQ

1. **Can I still use `BaseEntity`?** Only when an external project explicitly depends on it; it is not a current ddd4j-core contract.
2. **Must `AggregateRoot` use event sourcing?** No — but do not mix the two modes on the same aggregate.
3. **Can `Query` reference a PO?** Yes, via an explicit persistence scope. The domain `Query` itself binds to the aggregate root.
4. **Is `Repository` MyBatis-specific?** No — it is an ORM-agnostic SPI.
5. **Must `DomainService` be a Spring Bean?** Cannot be assumed across runtimes.
6. **What counts as proof of completion?** Current branch source, related tests, and verified runtime adapter behavior.

## Deep Reference

- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)
