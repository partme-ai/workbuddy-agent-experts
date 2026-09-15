---
name: ddd4j-architecture
description: Use when designing, reviewing, or locating boundaries in ddd4j modules, DDD/CQRS layers, ports and adapters, runtime integrations, or dependency direction. 中文触发词：模块边界、依赖方向、端口与适配器、DDD/CQRS 分层、运行时集成、架构评审。
license: Apache-2.0
---

# ddd4j Architecture

## Overview

ddd4j's stable center is the framework-agnostic domain, CQRS, and SPI layer. The outer modules deliver data, messaging, web, authentication, caching, observability, and runtime adapters.

## When to Use

- Deciding which module should own a new capability, port, or adapter.
- Reviewing dependency direction — whether the domain layer imports framework types.
- Tracing a core port (`CommandBus`, `Publisher`, `SubjectProvider`, `Repository`) to its actual registered adapter.
- Deciding whether a new broker, ORM client, or HTTP integration belongs in core or in a capability module.
- Reviewing how Spring, Guice, and Quarkus CDI share the same core contracts.
- Landing a new capability: where it goes, what registers it, and what proves it works.

## When NOT to Use

Do not use this skill when:

- **The semantics of `AggregateRoot`, `Command`, `Query`, or `DomainEvent` themselves are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Which Maven artifact owns a version, or BOM import order is the question** — use `ddd4j-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-bom`.
- **A concrete adapter must be implemented** (persistence, broker, HTTP, cache, auth) — use that dimension's skill: `ddd4j-data`, `ddd4j-mq`, `ddd4j-web`, `ddd4j-cache`, or `ddd4j-auth`.
- **Generic DDD methodology is the question** (bounded contexts, event storming, layering theory) with no ddd4j involvement — use the generic `ddd-skills` instead; do not force ddd4j module names onto a methodology discussion.
- **The project is not on ddd4j** — use the generic `java-skills`; retrofitting ddd4j module structure onto a foreign codebase is out of scope.
- **You should not conclude an implementation exists from directory names alone** — this skill requires call-graph and registration evidence; a folder listing is not a finding.

## Trigger Keywords

**English**: module boundaries, dependency direction, ports and adapters, layering, runtime integration, architecture review, landing a capability

**中文**: 模块边界, 依赖方向, 端口与适配器, 分层设计, 运行时集成, 架构评审, 能力落位

## Quick Start

- "Can the domain layer depend on a MyBatis Wrapper?"
- "Which module should assemble the CommandBus?"
- "Should a new broker live in core or in the mq module?"
- "How do Spring, Guice, and Quarkus CDI share the core contracts?"

## Architecture Zones

| Zone | Responsibility |
|---|---|
| annotation | DDD / CQRS / API / ORM metadata |
| core | AggregateRoot, Command/Query, Event, Repository, Context, SPI |
| kit | Foundational utilities, no business runtime |
| auth / data / mq / web / cache / metrics | Capability interfaces and their implementations |
| runtime-* | DI and lifecycle wiring for Spring, Guice, Quarkus, etc. |
| extensions | Cross-cutting optional extensions |
| ddd-rules | Architecture constraints and static checks |
| parent / dependencies / bom | Build, version ownership, and consumer surface |

## Decision Rules

1. Domain depends only on core, annotation, and necessary value types.
2. ORM, broker, HTTP, and authentication frameworks live in the adapter layer.
3. Static facades resolve implementations through Contexts, Registry, or SPI.
4. Framework runtimes own registration, request scoping, rollback, and shutdown.
5. BOM manages versions only — it does not prove runtime wiring succeeded.
6. The same aggregate must not mix snapshot Active Record with Event Sourcing.

## Capability Boundaries

### ✅ Strong At

- Module ownership and dependency direction.
- DDD / CQRS layering with ports and adapters.
- Sharing the core across multiple runtimes.
- Architecture review and landing new capabilities.

### ⚠️ Needs Input

- Target maintenance line and module POMs.
- Business behavior and transaction boundaries.
- Runtime and deployment model.

### ❌ Out of Scope

- Detailed framework API explanations.
- Concluding implementation from directory names alone.
- Unverified cross-line parity claims.

## Workflow

1. Confirm the Git root, branch, and CodeGraph health.
2. Trace core ports and their actual adapters from the call graph.
3. Mark compile dependencies, runtime registrations, and resource lifecycles.
4. Verify separately with architecture tests, behavior tests, and runtime evidence.
5. Report facts, inferences, violations, and proposed landing points.

## Workflow

### Step 1: Confirm the source of truth

Identify the Git root, branch, and maintenance line, and verify CodeGraph health. If the graph is unavailable, fall back to text search and say so in the report.

### Step 2: Map the dependency graph

Enumerate compile-time dependencies between modules and confirm arrows flow from adapters toward core ports. Flag any domain module importing `org.springframework.*`, `com.baomidou.mybatisplus.*`, `io.javalin.*`, or `io.quarkus.*`.

### Step 3: Trace the runtime wiring

For each SPI port (`CommandBus`, `Publisher`, `SubjectProvider`, `Repository`), find the concrete adapter registered by the runtime module. Document request-scope binding, shutdown hooks, and whether context cleanup covers success, exception, and async paths.

### Step 4: Validate behavior separately

Run architecture tests (`ddd-rules`), behavior tests over one end-to-end command path, and collect runtime evidence. Compile dependencies, runtime registrations, and resource lifecycles are three different claims — verify each on its own.

### Step 5: Report facts and gaps

Report current branch, modules, ports, adapters, registration points, tests, and risks. Label inferences explicitly and never merge them with facts; state missing implementations instead of inventing a chain.

## Gotchas

- Domain importing Spring, MyBatis, Javalin, or Quarkus types — this compiles fine and passes unit tests; only an import audit or `ddd-rules` architecture test catches it.
- Concrete broker or database clients created inside core — the class exists and works, which makes the violation invisible until the core module is reused on another runtime.
- A missing runtime registration misdiagnosed as a missing core API — the port exists; the static facade (`Contexts`/`Registry`) just returns empty because the runtime never wired it.
- Module and directory names treated as functional evidence — an `mq` directory does not prove a broker adapter registers, initializes, or closes anything.
- Reading the dependency tree without reading call sites and lifecycle — a dependency in the POM says nothing about whether it is registered, scoped, or closed at runtime.

## Output and Exceptions

Return `current branch, modules, ports, adapters, registration points, tests, risks`. When an implementation is missing, return `missing: specific adapter or registration point; how to provide: module or runtime` — never invent a fictitious chain.

## Deep Reference

- [Module Boundaries](references/module-boundaries.md)
- [Dependency Rules](references/dependency-rules.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Architecture evidence must not include credentials, real tenant data, or private Maven repository authentication. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；架构报告仅使用脱敏的模块与路径信息。

## Audience and Customization

- Developers: provide the target modules, runtime, and behavior.
- Architects: specify a read-only boundary, migration, or compatibility review.
- Testers: specify the required evidence levels.

Customize the target maintenance line, allowed dependencies, and output depth. When input is insufficient, give a tentative verdict first, then list `missing: module or runtime; how to provide: POM and call site`.

## FAQ

1. **Are skills organized by module?** No — by decision domain.
2. **Does a directory's existence mean the capability is complete?** No.
3. **Can the domain layer depend on a framework?** It should not.
4. **What does the runtime layer do?** Registration and lifecycle.
5. **Does identical cross-line structure imply identical behavior?** No.
6. **What if an implementation is missing?** State the gap explicitly; do not invent one.
