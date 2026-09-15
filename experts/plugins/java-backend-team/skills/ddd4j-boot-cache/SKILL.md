---
name: ddd4j-boot-cache
description: Use when configuring ddd4j caches in Spring Boot with local providers, Redis, Redisson, JetCache, TTL, CAS, idempotency, and readiness behavior. 中文触发词：缓存、本地缓存、Redis、Redisson、JetCache、TTL、CAS、幂等。
license: Apache-2.0
---

# ddd4j-boot Cache

## Overview

Covers Caffeine/Guava/Hutool, Redis, Redisson, JetCache, TTL, CAS, and idempotency uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Choosing among Caffeine/Guava/Hutool (local), Redis, Redisson, and JetCache for a ddd4j-boot service, matched to the consistency target.
- Wiring the cache auto-configuration so the domain's `Cache` SPI resolves to the assembled provider.
- Setting TTL units, capacity, and key strategy — and confirming the units actually mean what the configuration claims.
- Verifying atomic semantics the provider must prove: CAS compare-and-set contention and idempotency keys across instances.
- Overriding cache defaults with user beans or diagnosing why an unexpected cache bean is assembled.
- Diagnosing cache failures on a specific Boot line (2.3–4.1): beans present but Redis unreachable, TTL behaving differently than configured, invalidation not propagating.

## When NOT to Use

Do not use this skill when:

- **The `Cache` SPI contract itself needs changing** — use `ddd4j-cache` or `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cache`.
- **Generic auto-configuration mechanics are the question, not caching** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The runtime is Javalin or Quarkus** — use the matching `ddd4j-javalin-cache` or `ddd4j-quarkus-cache` skill instead; the Boot assembly does not transfer.
- **The project is plain Spring Boot without ddd4j** — generic Spring Cache / Redisson / JetCache skills apply; the `Cache` SPI assembly does not exist there.
- **The question is which version of the cache client to pin** — use `ddd4j-boot-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-bom`.
- **A "cache the domain aggregate" design is being invented** — do not use this skill to add caching the domain contract never asked for; check the core `Cache` SPI rules first.

## Trigger Keywords

**English**: cache, local cache, Redis, Redisson, JetCache, TTL, CAS, idempotency

**中文**: 缓存, 本地缓存, Redis, Redisson, JetCache, TTL, CAS, 幂等
## Core Scope

Caffeine/Guava/Hutool, Redis, Redisson, JetCache, TTL, CAS, idempotency.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among cache implementations and Spring Boot assembly.
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

Run `ddd4j-boot-version-selection` to fix the line, then locate the cache AutoConfiguration, its Properties, and the corresponding `ddd4j-cache` modules on that line.

### Step 2: Select the provider

Match local (Caffeine/Guava/Hutool), Redis, Redisson, or JetCache to the consistency target — a local cache and a distributed cache are different consistency contracts, not performance knobs. Confirm TTL units, capacity, and the key strategy.

### Step 3: Verify the wiring

Check conditional wiring, default beans, and user bean override points. Confirm the off switch truly skips assembly, and that connections (Redis client, pool) have explicit owners with failure rollback and idempotent close.

### Step 4: Test the semantics

Execute context tests plus TTL expiry, invalidate, and concurrency behavior. Cover Redis round-trips and CAS contention against a real backend — a local Map double cannot prove cross-instance atomicity.

### Step 5: Report with separated evidence

Report the chosen provider with configuration keys, the AutoConfiguration entry and override points, test results, and evidence state — configuration presence, bean creation, behavior, CI, and publish reported separately — plus risks and missing inputs.

## Gotchas

- A started context does not prove the Redis backend is reachable or that TTL behaves as configured — bean creation and cache behavior are different evidence layers.
- A local Caffeine cache and a Redis cache have different cross-instance semantics; the domain's `Cache` SPI requires the implementation to prove atomic semantics, and swapping providers silently changes them.
- TTL unit mismatches (seconds versus milliseconds) pass wiring tests and surface only as production staleness or premature eviction — confirm units from the line's Properties, not from intuition.
- A user-declared cache bean silently replaces the assembled default via `@ConditionalOnMissingBean`, changing invalidation and atomicity behavior that was never re-tested.
- A `destroyMethod` that never runs leaks Redis connections and client threads on context close — visible only in restart/rollback scenarios.
- CAS and idempotency against a single-node fake pass trivially; contention behavior only exists against a real (or realistically clustered) backend.
- Printing cache configuration for troubleshooting can leak endpoints and credentials — sensitive values must be redacted.

## Output and Exceptions

When information is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output credentials, tokens, production connection strings, or sensitive business data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例键值均为脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-boot-cache` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-cache` to review existing usage against the current source."
- "Use `$ddd4j-boot-cache` to return an implementation choice, evidence state, and remaining risk."

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
