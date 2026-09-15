---
name: ddd4j-quarkus-runtime
description: Use when integrating ddd4j with Quarkus CDI and Arc, including CommandBus, DomainEventPublisher, SubjectProvider, context, startup observers, duplicate registration, readiness, and shutdown. 中文触发词：CDI/Arc 集成、CommandBus、DomainEventPublisher、SubjectProvider、请求上下文、启动和关闭、就绪检查、重复注册。
license: Apache-2.0
---

# ddd4j-quarkus Runtime

## Overview

Covers CDI/Arc, CommandBus, DomainEventPublisher, SubjectProvider, Context, and startup/shutdown uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Producing `CommandBus`, `DomainEventPublisher`, or `SubjectProvider` beans for ddd4j SPIs via CDI producers or BuildItems in a Quarkus application.
- Binding request-scoped `Context` and restoring it on success, exception, and async completion paths.
- Owning ddd4j resource lifecycle with startup/shutdown observers: drain, reverse-order close, idempotent close.
- Diagnosing duplicate SPI registrations or an Arc `unsatisfied dependency` build failure for a ddd4j port.
- Aggregating readiness from real dependencies instead of a hardcoded state.
- Reviewing an application's Arc wiring against Quarkus (not Spring) registration semantics on either line.

## When NOT to Use

Do not use this skill when:

- **Authoring a new extension with Processor, BuildItems, or Recorder** — use `ddd4j-quarkus-extension-authoring` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-extension-authoring`; do not use this skill to write build steps.
- **Choosing or wiring an authentication mechanism (JWT, OIDC, Shiro, Sa-Token)** — use `ddd4j-quarkus-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-auth`.
- **The SPI contracts themselves (CommandBus dispatch semantics, DomainEvent publication rules)** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Spring Boot auto-configuration wiring of the same SPIs** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **Javalin wiring of the same SPIs** — use `ddd4j-javalin-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-runtime`.
- **The project is a plain Quarkus application without ddd4j** — generic Quarkus/Arc guidance applies; do not use the ddd4j SPI port list on a non-ddd4j stack.

## Trigger Keywords

**English**: CDI Arc wiring, CommandBus, DomainEventPublisher, SubjectProvider, request context, startup shutdown observers, readiness check, duplicate registration

**中文**: CDI/Arc 集成, CommandBus, DomainEventPublisher, SubjectProvider, 请求上下文, 启动和关闭, 就绪检查, 重复注册

## Core Scope

CDI/Arc, CommandBus, DomainEventPublisher, SubjectProvider, Context, startup/shutdown.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for the runtime and Quarkus adaptation.
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

Fix the line via `ddd4j-quarkus-version-selection`, then locate `runtime-quarkus`, its configuration, and the Arc tests in that checkout. Registration idioms are per line.

### Step 2: Register the SPI ports

Produce `CommandBus`, `DomainEventPublisher`, and `SubjectProvider` beans via producers/BuildItems, and fail fast on duplicate registrations — a second producer for the same port is a wiring bug, not a fallback.

### Step 3: Bind request context

Establish request-scoped `Context` binding and restoration on success, exception, and async completion, and confirm startup/shutdown observers own the resource lifecycle rather than constructors.

### Step 4: Verify readiness and shutdown

Aggregate readiness from real dependencies and confirm drain and idempotent close, including native image boundaries where the deployment target requires them.

### Step 5: Verify

Run Arc/QuarkusTest suites covering startup, request context, shutdown, and duplicate registration, then produce a report with registration points, lifecycle owners, evidence state, and remaining risk.

## Gotchas

- CDI bean discovery in Quarkus is build-time: Arc validates injection points during the build, so a missing bean-defining annotation or producer is a build failure — there is no runtime lookup that can recover.
- A class present in source but never discovered produces no bean; "the class exists in our codebase" is not evidence a `CommandBus` producer is registered.
- Two producers for the same SPI port surface as an ambiguous-resolution build failure, not a silent "last one wins" — which is why duplicate registrations should fail fast by design.
- A request-scoped `Context` released only on the success path leaks the previous request's Subject onto pooled worker threads; the exception and async-completion paths each need their own restore.
- Resource lifecycle belongs in startup/shutdown observers; logic placed in a bean constructor runs before readiness and cannot be undone by close-on-shutdown logic alone.
- Native image requires explicit registration; reflection-based context propagation that works in JVM mode can fail at native build.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；Subject 与租户示例均为脱敏虚构数据。

## Quick Start

- "Use `$ddd4j-quarkus-runtime` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-runtime` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-runtime` to return an implementation choice, evidence state, and remaining risk."

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
