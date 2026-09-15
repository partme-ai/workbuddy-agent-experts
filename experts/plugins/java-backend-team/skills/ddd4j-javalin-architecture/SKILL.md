---
name: ddd4j-javalin-architecture
description: Use when designing or reviewing ddd4j-javalin module boundaries, parent/BOM layering, runtime composition, auth, data, MQ, Web, cache, extensions, testcontainers, or samples. 中文触发词：模块边界、集成边界、依赖方向、BOM 分层、运行时组合。
license: Apache-2.0
---

# ddd4j-javalin Architecture

## Overview

Covers parent, bom, dependencies, core, ddd, auth, data, mq, web, cache, extensions, and testcontainers uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Designing or reviewing the module set — parent, bom, dependencies, core, ddd, auth, data, mq, web, cache, extensions, testcontainers — on any maintenance line (6.7.x, 7.1.x, or 7.2.x).
- Checking dependency direction between modules: adapters may depend on core SPIs, never the reverse.
- Reviewing how `Ddd4jJavalinRuntime` composes the auth, data, MQ, web, and cache providers.
- Deciding where a new module, sample, or test-support module belongs in the parent/BOM layering.
- Auditing cross-module guarantees such as Context/Subject/resource cleanup on success, exception, and async terminal states.

## When NOT to Use

Do not use this skill when:

- **One module's internals must be implemented or fixed** — use the matching capability skill such as `ddd4j-javalin-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-data`.
- **The maintenance line itself must be chosen or verified** — use `ddd4j-javalin-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-version-selection`.
- **A cross-capability review, plan approval, or release gate is needed** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **Core domain or SPI contracts (`AggregateRoot`, `Command`, `Repository`) are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Spring Boot module layering is the question** — use `ddd4j-boot-architecture` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-architecture`. Quarkus: `ddd4j-quarkus-architecture`; Spring Cloud: `ddd4j-cloud-architecture`.
- **The project is a plain Javalin or generic Java multi-module build without ddd4j** — do not use this skill; use `java-skills` instead, since no ddd4j module contract applies.

## Trigger Keywords

**English**: module boundaries, integration boundaries, dependency direction, BOM layering, runtime composition, module layering, parent POM

**中文**: 模块边界, 集成边界, 依赖方向, BOM 分层, 运行时组合, 模块划分, 父 POM

## Core Scope

parent, bom, dependencies, core, ddd, auth, data, mq, web, cache, extensions, testcontainers.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for architecture and Javalin adaptation.
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

### Step 1: Confirm the line and source of truth

Fix the maintenance line (6.7.x, 7.1.x, or 7.2.x) with `ddd4j-javalin-version-selection`, then confirm the branch, SHA, and current checkout state before reading any module.

### Step 2: Map the modules

Enumerate parent, bom, dependencies, core, ddd, auth, data, mq, web, cache, extensions, and testcontainers. For each, confirm the dependency direction and the line's Javalin/JDK/Maven/POM contract.

### Step 3: Verify composition

Trace how the runtime composes the auth, data, MQ, web, and cache providers, and confirm Context/Subject/resource cleanup on success, exception, and async terminal states. Composition order is also shutdown order.

### Step 4: Validate behavior

Run the line's contract and behavior tests. For production paths, confirm real readiness aggregation, shared CAS idempotency, and explicit CORS — not just their presence in source.

### Step 5: Report findings

Produce a single report: line, modules inspected, entry points with file paths, composition and lifecycle ownership, tests executed with evidence state per tier, and violations with proposed fixes.

## Gotchas

- `JavalinLifecycleParticipant` shutdown runs in reverse registration order — modules registered early must close last, so composition order is also a shutdown contract.
- The testcontainers module is test-scope support; a production module depending on it at compile scope silently drags Docker test machinery into the artifact.
- Parent/BOM layering must match the line's POM model — Maven 3 `<modules>` versus Maven 4 `<subprojects>` — and normalizing all lines to one model is a contract break, not cleanup.
- A module compiling is not a boundary check; dependency direction is proven by POM inspection and executed contract tests, not by a green build.
- Javalin 6 and Javalin 7 APIs differ — module code copied across maintenance lines must be re-verified on each line even when the class names match.
- Extensions compose through Guice `Modules.override`; a business binding installed before the default module it overrides is silently ignored, and the service still starts.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；架构评审示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-architecture` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-architecture` to review existing usage against the current source."
- "Use `$ddd4j-javalin-architecture` to return an implementation choice, evidence state, and remaining risk."

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
