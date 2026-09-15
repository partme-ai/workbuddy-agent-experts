---
name: ddd4j-quarkus-cache
description: Use when integrating Quarkus Cache, Redis, or ddd4j Cache SPI with Quarkus, including TTL, CAS, idempotency, bean scopes, and lifecycle. 中文触发词：缓存集成、Quarkus Cache、Redis、Cache SPI、TTL、CAS、幂等、缓存作用域、生命周期。
license: Apache-2.0
---

# ddd4j-quarkus Cache

## Overview

Covers Quarkus Cache, Redis, the ddd4j Cache SPI, TTL, CAS, idempotency, and CDI scope uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Choosing among Quarkus Cache, Redis, and the ddd4j `Cache` SPI against the service's consistency target.
- Using shared CAS for multi-instance idempotency (replay protection across replicas).
- Registering cache providers with correct CDI scopes and configuration mappings.
- Owning cache connection lifecycle: startup/shutdown observers and idempotent close.
- Testing TTL, invalidate, concurrency, and real CAS contention with QuarkusTest.
- Reviewing existing cache wiring — scopes, eviction versus idempotency keys, native compatibility — on the 3.3.x or 4.0.x line.

## When NOT to Use

Do not use this skill when:

- **Spring Boot caching (Spring Cache, Redisson, JetCache)** — use `ddd4j-boot-cache` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-cache`; Spring Cache abstractions must not be mixed into a ddd4j-quarkus line.
- **Javalin caching** — use `ddd4j-javalin-cache` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-cache`.
- **The `Cache` SPI contract itself (cross-instance atomic semantics) is the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Endpoint-level idempotency design (key headers, replay responses)** — use `ddd4j-quarkus-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-web`; this skill owns the CAS backend, the web skill owns the HTTP contract.
- **The project is plain Quarkus without ddd4j** — generic Quarkus Cache/Redis guidance applies; do not use the ddd4j Cache SPI model on a non-ddd4j stack.
- **Data access and persistence are the actual topic** — use `ddd4j-quarkus-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-data`.

## Trigger Keywords

**English**: cache integration, Quarkus Cache, Redis, Cache SPI, TTL, CAS, idempotency, cache CDI scope, cache lifecycle

**中文**: 缓存集成, Quarkus Cache, Redis, Cache SPI, TTL, CAS, 幂等, 缓存作用域, 生命周期

## Core Scope

Quarkus Cache, Redis, ddd4j Cache SPI, TTL, CAS, idempotency, CDI scope.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for caching and Quarkus adaptation.
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

Fix the line via `ddd4j-quarkus-version-selection`, then locate `ddd4j-quarkus-cache` and the cache tests in that checkout. The supported providers and config keys are per line.

### Step 2: Select the provider

Compare Quarkus Cache, Redis, and the ddd4j `Cache` SPI against the consistency target, and use shared CAS wherever multi-instance idempotency is required — a local cache cannot provide it.

### Step 3: Wire CDI and lifecycle

Register cache providers with correct CDI scopes and configuration mappings, and confirm startup/shutdown observers own the connections with idempotent close.

### Step 4: Test the semantics

Run QuarkusTest suites for TTL, invalidate, concurrency, and real CAS contention, and verify native image compatibility where the contract requires it.

### Step 5: Report

Produce a single report: provider choices with configuration keys and CDI scopes, lifecycle owners and registration points, tests executed and evidence state per tier, and risks with proposed fixes and missing inputs.

## Gotchas

- The `Cache` SPI only delivers cross-instance atomic semantics (CAS) if the implementation proves it — a local Caffeine-backed implementation passes unit tests and breaks on the second replica.
- CDI scope matters: a cache provider registered `@Dependent` is recreated per injection point, silently forking caches that were meant to be shared.
- Quarkus Cache provider and TTL configuration is build-time fixed; a runtime-profile override does not rewire the provider or the eviction window.
- Idempotency keys sharing a cache with short TTL inherit eviction — an evicted key disables replay protection, so idempotency storage needs its own TTL budget.
- Native image requires explicit registration for cached payload reflection/serialization; JVM-mode cache tests pass while the native build fails on the first cached type.
- Connection close must be idempotent and owned by a shutdown observer; a double close (observer plus framework) masks the real shutdown error.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；缓存键与配置示例均为脱敏虚构数据。

## Quick Start

- "Use `$ddd4j-quarkus-cache` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-cache` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-cache` to return an implementation choice, evidence state, and remaining risk."

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
