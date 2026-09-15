---
name: ddd4j-javalin-cache
description: Use when selecting or wiring local and distributed ddd4j caches in Javalin, including Caffeine, shared CAS, idempotency, TTL, lifecycle, and production validation. 中文触发词：本地缓存、分布式缓存、CAS、TTL、幂等后端、Caffeine。
license: Apache-2.0
---

# ddd4j-javalin Cache

## Overview

Covers Caffeine, local caches, distributed Cache, shared CAS, TTL, and idempotency uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Selecting between Caffeine local caches and a distributed Cache with shared CAS for a ddd4j-javalin service on 6.7.x, 7.1.x, or 7.2.x.
- Deciding the idempotency backing: Caffeine explicitly as a single-instance/development fallback, shared CAS for multi-instance production.
- Configuring TTL, invalidation, and concurrency behavior for local providers, and lock contention/retry behavior for the distributed provider.
- Registering cache providers as lifecycle participants with explicit owners, readiness contribution where required, and idempotent close.
- Validating production behavior: real CAS contention, retries, and TTL re-acquisition against the shared backend — not a local fake.

## When NOT to Use

Do not use this skill when:

- **The HTTP idempotency filter and replay responses on routes are the question** — use `ddd4j-javalin-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-web`.
- **Lifecycle participant mechanics (ordering, rollback, hooks) are the question** — use `ddd4j-javalin-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-runtime`.
- **The framework-agnostic `Cache` SPI contract is the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **A cross-capability review or release gate is needed** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **Spring Boot or Quarkus cache wiring is the question** — use `ddd4j-boot-cache` or `ddd4j-quarkus-cache` instead, for example Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-cache`. Spring Cloud cache composition: `ddd4j-cloud-architecture`.
- **The project tunes plain Caffeine or Redis without ddd4j** — do not use this skill; use `java-skills` instead, since the ddd4j `Cache` SPI and shared-CAS contract do not exist there.

## Trigger Keywords

**English**: local cache, distributed cache, CAS, TTL, idempotency backend, Caffeine, cache lifecycle

**中文**: 本地缓存, 分布式缓存, CAS, TTL, 幂等后端, Caffeine, 缓存生命周期

## Core Scope

Caffeine, local caches, distributed Cache, shared CAS, TTL, idempotency.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for caching and Javalin adaptation.
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

Fix the maintenance line with `ddd4j-javalin-version-selection`, then locate the cache module and the web idempotency tests in the current checkout.

### Step 2: Select the provider

Use Caffeine only for single-instance or development deployments, with explicit configuration and a documented fallback status. Use a distributed cache with shared CAS wherever multi-instance production idempotency is required.

### Step 3: Wire the lifecycle

Register cache providers as lifecycle participants with explicit owners and idempotent close. Confirm readiness reflects cache backend availability where the deployment contract requires it.

### Step 4: Test against the real backend

Verify TTL, invalidate, and concurrency for local providers. For the distributed provider, verify real CAS contention, retries, and TTL re-acquisition against the shared backend — a local fake that never contends proves nothing.

### Step 5: Report the cache state

Produce a single report: provider choices with configuration keys, lifecycle registration and shutdown order, tests executed with evidence state per tier, and risks with proposed fixes and missing inputs.

## Gotchas

- Caffeine-backed idempotency is a single-instance fallback only; multi-instance production needs shared CAS — two replicas each holding their own key set deduplicate nothing across instances.
- CAS correctness must be proven against the real shared backend; a local fake that never contends cannot expose lost locks or TTL re-acquisition failures.
- `JavalinLifecycleParticipant` shutdown runs in reverse registration order; a cache registered early must close last, and close must be idempotent.
- Readiness should reflect cache backend availability where required — a silent READY hides a degraded CAS until the first duplicate write slips through.
- TTL re-acquisition failure (the lock is lost mid-operation) needs an explicit path; silently proceeding is a duplicate waiting to happen.
- The maintenance lines do not change Caffeine semantics, but the per-line POM/JDK contract still governs the module — do not copy 7.2.x-only syntax into older lines.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；缓存示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-cache` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-cache` to review existing usage against the current source."
- "Use `$ddd4j-javalin-cache` to return an implementation choice, evidence state, and remaining risk."

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
