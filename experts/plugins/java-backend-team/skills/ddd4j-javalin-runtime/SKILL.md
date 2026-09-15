---
name: ddd4j-javalin-runtime
description: Use when implementing or reviewing ddd4j-javalin startup, configuration validation, SPI registration, lifecycle participants, readiness, drain, rollback, shutdown hooks, or close behavior. 中文触发词：启动流程、生命周期、SPI 注册、就绪检查、Drain、回滚、Hook、优雅关闭。
license: Apache-2.0
---

# ddd4j-javalin Runtime

## Overview

Covers start, validate, initialize, SPI, readiness, drain, rollback, shutdown hook, and close uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Implementing or reviewing `Ddd4jJavalinRuntime` and its `start → validate → initialize → ready → drain → close` path on 6.7.x, 7.1.x, or 7.2.x.
- Designing rollback after partial initialization: which `JavalinLifecycleParticipant`s were initialized and in what reverse order they must close.
- Registering SPI providers and lifecycle participants, including required-versus-optional dependency semantics and readiness contribution.
- Implementing real configuration loading and startup validation that rejects invalid production configuration instead of falling back to defaults.
- Fixing shutdown-hook accumulation across repeated starts or embedded tests, or making `close()` idempotent.
- Separating aggregated readiness (DB, MQ, OIDC, Outbox) from process-only liveness.

## When NOT to Use

Do not use this skill when:

- **HTTP behavior served by the runtime is the question (routes, CORS, errors, idempotency)** — use `ddd4j-javalin-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-web`.
- **A specific participant's internals are the question (EMF/Outbox, MQ consumers, auth provider)** — use `ddd4j-javalin-data`, `ddd4j-javalin-mq`, or `ddd4j-javalin-auth` instead for the matching capability skill.
- **A cross-capability review, plan approval, or release gate is needed** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **Core domain or lifecycle SPI contracts are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Spring Boot auto-configuration and startup wiring is the question** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`. Quarkus runtime: `ddd4j-quarkus-runtime`; Spring Cloud lifecycle: `ddd4j-cloud-architecture`.
- **The project is a plain Javalin embedded server without ddd4j** — do not use this skill; use `java-skills` instead, since `Ddd4jJavalinRuntime` and its participant SPI do not exist there.

## Trigger Keywords

**English**: startup lifecycle, SPI registration, readiness, drain, rollback, shutdown hook, graceful close, lifecycle participants

**中文**: 启动流程, 生命周期, SPI 注册, 就绪检查, Drain, 回滚, Hook, 优雅关闭

## Core Scope

start, validate, initialize, SPI, readiness, drain, rollback, shutdown hook, close.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for the runtime and Javalin adaptation.
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

Fix the maintenance line with `ddd4j-javalin-version-selection`, then locate `Ddd4jJavalinRuntime`, its lifecycle participants, and their tests in the current checkout.

### Step 2: Review the lifecycle path

Verify the coherent `start → validate → initialize → ready → drain → close` sequence, rollback of initialized resources in reverse order after partial failure, and that close is idempotent with no accumulating shutdown hooks.

### Step 3: Verify readiness and context

Confirm readiness aggregates required and optional participants while liveness stays process-only, and that Context/Subject cleanup happens on success, exception, and async terminal states.

### Step 4: Test the lifecycle

Exercise startup success, partial failure with rollback, restart, and repeated starts in embedded tests. Run behavior tests for configuration validation and SPI registration, not just happy-path construction.

### Step 5: Report the lifecycle state

Produce a single report: lifecycle path with registration and ownership points (file paths and line numbers), readiness contributors with required/optional classification, tests executed with evidence state per tier, and violations with proposed fixes.

## Gotchas

- `JavalinLifecycleParticipant` shutdown runs in reverse registration order; resources created first must close last.
- A shutdown hook registered per start accumulates across embedded tests and repeated starts — one hook per process, or proven removal on every stop.
- Readiness must aggregate real dependencies (DB, MQ, OIDC, Outbox); liveness must remain process-only — conflating them turns every downstream outage into a restart storm.
- Rollback after partial initialization must close only the participants that actually initialized, in reverse order; closing an uninitialized participant masks the real failure.
- `close()` must be idempotent: drain and embedded-test teardown invoke it more than once by design.
- Real configuration loading and startup validation are required — default-object construction plus port parsing silently accepts broken production configuration.
- Javalin 6 and Javalin 7 APIs differ — startup and lifecycle code copied between maintenance lines must be re-verified per line.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；生命周期示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-runtime` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-runtime` to review existing usage against the current source."
- "Use `$ddd4j-javalin-runtime` to return an implementation choice, evidence state, and remaining risk."

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
