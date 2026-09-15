---
name: ddd4j-runtime
description: Use when integrating or reviewing ddd4j runtime bindings for Spring, Guice, Quarkus CDI, Micronaut, Vert.x, Helidon, or Dropwizard, including SPI registration, context, buses, publishers, readiness, startup rollback, and shutdown. 中文触发词：运行时集成、SPI 注册、依赖注入、启动回滚、就绪检查、上下文绑定、优雅关闭、Guice Module。
license: Apache-2.0
---

# ddd4j Runtime

## Overview

The runtime binds framework containers to the ddd4j core ports; core does not depend on any DI framework, and the runtime owns unique registration, request scope, and resource lifecycle.

## When to Use

- Registering core SPIs — `CommandBus`, `DomainEventPublisher`, `SubjectProvider`, `Cache`, `Repository` — into Spring, Guice, Quarkus CDI, Micronaut, Vert.x, Helidon, or Dropwizard.
- Establishing Request/Thread/Reactive `Context` binding with restore on every terminal state.
- Designing startup ordering, dependency ordering between providers, and aggregated readiness.
- Handling partial startup failure: rolling back already-created resources in reverse order.
- Diagnosing duplicate registrations or missing entries behind `Contexts` / `Registry` / `SubjectKit`.
- Verifying runtime behavior with runtime-testkit plus the target framework's own tests.

## When NOT to Use

Do not use this skill when:

- **The Subject/auth chain semantics are the question** (providers, tokens, roles) — use `ddd4j-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-auth`; this skill only wires the registration and scope.
- **HTTP behavior of the web adapter is the question** — use `ddd4j-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-web`.
- **Repository/EventStore implementations are the question** — use `ddd4j-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-data`.
- **A request applies Spring annotations or Spring lifecycle assumptions to every runtime** — do not use this skill for that; each runtime has its own registration points, and porting Spring semantics across runtimes is an explicit anti-pattern.
- **Generic DI-framework usage (a plain Guice/Spring app with no ddd4j ports involved)** — use the generic `java-skills` or framework-specific skills.

## Trigger Keywords

**English**: runtime integration, SPI registration, dependency injection, startup rollback, readiness check, context binding, graceful shutdown, Guice module

**中文**: 运行时集成, SPI 注册, 依赖注入, 启动回滚, 就绪检查, 上下文绑定, 优雅关闭, 启动顺序

## Runtimes

Spring, Guice, Quarkus CDI, Micronaut, Vert.x, Helidon, Dropwizard, plus runtime-testkit.

## Unified Responsibilities

- Register SPIs such as CommandBus, DomainEventPublisher, SubjectProvider, and Cache/Repository.
- Establish Request/Thread/Reactive Context.
- Initialize dependencies and aggregate readiness.
- Roll back in reverse order on partial failure.
- Idempotent close after drain.
- Prevent duplicate registration and shutdown hook leaks.

## Capability Boundaries

### ✅ Strong At

- DI/SPI assembly.
- Context and Subject lifecycle.
- Startup/readiness/drain/close.
- Behavior alignment across runtimes.

### ⚠️ Needs Input

- Target runtime and maintenance line.
- The SPIs that need registration.
- Resource dependencies and shutdown order.

### ❌ Out of Scope

- Applying Spring annotations to every runtime.
- Arbitrary overrides after duplicate registration.
- Declaring the runtime ready because a container started.

## Workflow

### Step 1: List the ports and providers

Enumerate every core port that needs a runtime binding — `CommandBus`, `DomainEventPublisher`, `SubjectProvider`, `Cache`, `Repository` — and the concrete provider for each. A port with no provider is a deferred failure, so the list is the design.

### Step 2: Define the dependency order

Order initialization so no provider starts before its dependencies (e.g. `SubjectProvider` before web binding, `Repository` before `CommandBus` handlers that use it). The runtime owns this ordering per framework idiom: Spring bean lifecycle, Guice `Module`/`Injector`, Quarkus CDI/Arc producers.

### Step 3: Register and detect duplicates

Bind each provider exactly once through the framework, with registration detecting duplicates and missing entries. A duplicate `CommandBus` executor type must fail fast — silent last-write-wins hides configuration errors until production.

### Step 4: Bind and restore the request context

Establish Request/Thread/Reactive `Context` at the entry point using a scope object that restores the previous values. Every terminal state — success, exception, async completion — must restore.

### Step 5: Aggregate readiness

Readiness must reflect real participants: registered ports, required listeners, dependency health. Never hardcode `READY`; a container that started is not a runtime that is ready.

### Step 6: Roll back, drain, close

On partial startup failure, close already-created resources in reverse order. On shutdown, drain in-flight work, then close idempotently — and avoid shutdown-hook leaks from repeated registrations.

### Step 7: Test with runtime-testkit and the target framework

Prove startup, readiness, context restore, rollback, and close with runtime-testkit plus the framework's native tests. Behavior must align across runtimes, not just work on one.

## Gotchas

- Static facades called before registration — `Contexts`/`Registry`/`SubjectKit` compile fine and return empty or throw at first use; the call site looks correct and the failure is a wiring-order problem.
- Later registrations silently overwriting earlier ones — two beans providing the same `CommandBus` executor type can boot cleanly with the wrong one winning; duplicates must fail fast, not last-write-wins.
- Partial startup leaks resources permanently — when provider 4 of 6 fails, providers 1–3's connections and pools keep running unless rollback closes them in reverse order.
- Spring timing assumptions ported to other runtimes — Spring's `afterSingletonsInstantiated` registration point has no direct equivalent in Vert.x or Helidon; per-runtime registration points come from the adapter source, not from Spring habits.
- Hardcoded `READY` — readiness returning true regardless of participant state turns every downstream degradation into a surprise discovered by traffic.
- Context residue across terminal states — a scope restored only on success leaves the previous request's Subject/tenant on pooled threads after exceptions or async completions.
- Non-idempotent close and shutdown-hook leaks — a runtime registered twice (e.g. hot redeploy) closes twice or registers duplicate hooks; close must tolerate repeated invocation.

## Deep Reference

- [Runtime Matrix](references/runtime-matrix.md)
- [SPI Registration](references/spi-registration.md)
- [Lifecycle](references/lifecycle.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

The Context must not leak Subject, Tenant, or Token across requests. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；上下文示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-runtime` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-runtime` to review existing usage against the current source."
- "Use `$ddd4j-runtime` to return an implementation choice, evidence state, and remaining risk."

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
