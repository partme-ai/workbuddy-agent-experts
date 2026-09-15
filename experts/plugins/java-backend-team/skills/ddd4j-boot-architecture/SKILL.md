---
name: ddd4j-boot-architecture
description: Use when designing or reviewing ddd4j-boot module boundaries, parent/BOM layering, Spring Boot integration responsibilities, starter aggregation, or dependencies between core, auth, data, MQ, Web, cache, and extensions. 中文触发词：模块边界、集成职责、parent/BOM 分层、聚合 POM、启动装配、依赖方向、维护线。
license: Apache-2.0
---

# ddd4j-boot Architecture

## Overview

Targets the current ddd4j-boot maintenance line: parent, dependencies, bom, core, auth, data, mq, web, cache, extensions, samples. Confirm the version line first, then apply this skill.

## When to Use

- Deciding which responsibilities belong in `ddd4j-boot-parent`, `ddd4j-boot-dependencies`, `ddd4j-boot-bom`, versus the concrete feature modules (core, auth, data, mq, web, cache, extensions).
- Reviewing whether a Boot module wrongly re-implements or copies `ddd4j-core` semantics instead of assembling them.
- Separating aggregator POMs from concrete implementation modules, or deciding whether something is a starter.
- Auditing that platform versions are owned by the BOM and have not leaked into concrete modules.
- Locating the auto-configuration entry points, default implementations, and user override points of a module.
- Reconciling architecture differences between two of the 13 maintenance lines (Boot 2.3–4.1).

## When NOT to Use

Do not use this skill when:

- **Domain contracts themselves (aggregates, commands, CQRS) are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **You are picking a Boot/JDK/Maven line or planning an upgrade** — use `ddd4j-boot-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-version-selection`.
- **The request is how a specific auto-configuration class is written or registered** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The runtime is Javalin, Quarkus, or Spring Cloud** — use the matching `ddd4j-javalin-*`, `ddd4j-quarkus-*`, or `ddd4j-cloud-*` architecture skill instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill <skill-name>`.
- **The project is plain Spring Boot without ddd4j** — generic Java / Spring Boot architecture skills apply; this module map should not be imposed on a non-ddd4j stack.
- **A concrete feature integration (data source, cache client, MQ binder) is the question** — use the matching `ddd4j-boot-data`, `ddd4j-boot-cache`, or `ddd4j-boot-mq` skill instead.

## Trigger Keywords

**English**: module boundaries, integration responsibilities, parent/BOM layering, aggregator POM, starter assembly, dependency direction, maintenance line

**中文**: 模块边界, 集成职责, parent/BOM 分层, 聚合 POM, 启动装配, 依赖方向, 维护线
## Core Scope

parent, dependencies, bom, core, auth, data, mq, web, cache, extensions, samples.

## Rules

1. The Boot layer only assembles ddd4j capabilities; it does not copy core implementations.
2. Aggregator POMs stay separate from concrete implementation modules.
3. Conditional wiring and lifecycle belong to the concrete feature modules.
4. Each maintenance line keeps its own JDK/Maven/POM.
5. A module existing does not mean the auto-configuration has taken effect.

## Capability Boundaries

### ✅ Strong At

- Boot-specific architecture and configuration decisions for the current line.
- Choosing among multiple implementations and dividing responsibilities.
- Maintenance-line differences and verification paths.

### ⚠️ Needs Input

- Target Boot line, JDK, Maven, and POM.
- Target module and runtime behavior.
- Current source/tests/CI status.

### ❌ Out of Scope

- Rewriting ddd4j core domain contracts.
- Treating dependency presence as runtime success.
- Automatically releasing or upgrading production projects.

## Workflow

### Step 1: Confirm the source of truth

Run `ddd4j-boot-version-selection` to fix the maintenance line, JDK, Maven, and POM model, then confirm the branch, SHA, and CodeGraph health. Architecture rules differ per line, so quoting the wrong line invalidates everything downstream.

### Step 2: Map the modules

Enumerate parent, dependencies, bom, core, auth, data, mq, web, cache, extensions, and samples in the target line. Separate aggregator POMs from concrete implementation modules — an aggregator POM is not a starter.

### Step 3: Verify assembly

For each AutoConfiguration, confirm the conditional wiring, the default implementations, and the user bean override points. Confirm platform versions stay in the BOM and have not leaked into concrete modules.

### Step 4: Validate behavior

Run the target module's context and behavior tests. Distinguish dependency resolution from bean creation evidence — a resolved artifact proves nothing about a created bean.

### Step 5: Report with layered evidence

Report the version line, modules inspected (with file paths), auto-configuration entry points, defaults and override points, tests executed, and evidence state — source, test, CI, and publish reported separately, each violation paired with a proposed fix.

## Gotchas

- A module existing in the BOM does not mean its auto-configuration is active — "module as behavior" is the canonical false positive. Only context or behavior tests prove assembly.
- Aggregator POMs look like starters but are not; treating one as the wiring entry point sends integration work to the wrong place.
- Platform versions drifted into concrete modules will resolve locally and break later — version ownership belongs to the BOM alone.
- A missing `@ConditionalOnMissingBean` check means defaults can silently override user configuration instead of the reverse; the override direction must be verified, not assumed.
- Counting a local build success as CI/publish evidence conflates layers; the same code can be locally green and remotely unbuildable.
- Boot modules should not copy or alter `ddd4j-core` semantics; they assemble. An old line cannot simply adopt a new line's annotations — each line adapts them individually.

## Output and Exceptions

Output the version line, modules, configuration entry points, default implementations, override points, tests, and risks. When input is missing, write "missing: target line or module; how to provide: supply the POM and behavior requirements".

## Deep Reference

- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output settings, tokens, passwords, or production connection information. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例均为脱敏的虚构模块与配置。

## Quick Start

- "Use `$ddd4j-boot-architecture` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-architecture` to review existing usage against the current source."
- "Use `$ddd4j-boot-architecture` to return an implementation choice, evidence state, and remaining risk."

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
