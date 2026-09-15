---
name: ddd4j-cloud-architecture
description: Use when designing or reviewing ddd4j-cloud parent, BOM, dependencies, extensions, compatibility tests, verification consumers, samples, and upstream Boot or ddd4j boundaries. 中文触发词：模块边界、上游边界、Cloud 扩展、兼容验证、验证消费者、维护线。
license: Apache-2.0
---

# ddd4j-cloud Architecture

## Overview

Covers parent, bom, dependencies, extensions, compatibility-tests, verification, samples, and upstream boundaries uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Reviewing the ddd4j-cloud module layout: parent, bom, dependencies, extensions, compatibility-tests, verification, samples.
- Deciding where a new extension belongs and which upstream Boot/ddd4j artifacts it may consume.
- Auditing extensions for canonical `extensions` naming with no old `cmpt` references.
- Reviewing upstream boundaries — what ddd4j-cloud consumes versus what it must not reimplement.
- Confirming at the architecture level that Context/Tenant restoration covers sync, async, Reactor, and Feign paths.
- Planning a read-only boundary review before a migration or fork merge.

## When NOT to Use

Do not use this skill when:

- **Which versions pair together is the question** — use `ddd4j-cloud-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-version-selection`.
- **BOM import order or version ownership inside the POMs is the question** — use `ddd4j-cloud-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-bom`.
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-architecture` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-architecture`.
- **Core domain or SPI contracts are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **A single capability needs concrete wiring** (Feign interceptors, Stream bindings, tenant rules) — use the matching `ddd4j-cloud-*` capability skill instead.
- **Generic Spring Cloud microservice architecture without ddd4j** — do not use this skill; apply generic `spring-cloud` guidance instead (no install command).
- **Releasing or publishing the lines is the goal** — use `ddd4j-cloud-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-release`.

## Trigger Keywords

**English**: module boundaries, upstream boundary, Cloud extensions, compatibility tests, verification consumers, module layout, maintenance line

**中文**: 模块边界, 上游边界, Cloud 扩展, 兼容验证, 验证消费者, 维护线

## Core Scope

parent, bom, dependencies, extensions, compatibility-tests, verification, samples, upstream boundaries.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for architecture and Spring Cloud integration.
- Upstream/downstream versions and cross-service boundaries.
- Differences across the eight maintenance lines.

### ⚠️ Needs Input

- Target Cloud line, Boot parent, and POM.
- Capabilities, external services, and deployment requirements.
- Current source/test/remote evidence.

### ❌ Out of Scope

- Treating README module names as completed capabilities.
- Substituting configuration presence for external service behavior.
- Unauthorized releases or production operations.

## Workflow

### Step 1: Confirm the source of truth

Run `ddd4j-cloud-version-selection` to fix the Cloud→Boot→ddd4j combination, then confirm the branch, checkout SHA, and CodeGraph health so the review reads the intended tree.

### Step 2: Map the modules

Enumerate parent, bom, dependencies, extensions, compatibility-tests, verification, and samples, with each module's entry points. Confirm extensions use canonical naming with no old `cmpt` references.

### Step 3: Verify upstream boundaries

Check which Boot/ddd4j artifacts the extensions consume and at which versions. Classify anything missing as BLOCKED(upstream) rather than reimplementing it inside ddd4j-cloud.

### Step 4: Validate behavior

Run the compatibility tests and verification consumers for the line, and confirm Context/Tenant restoration is covered on sync, async, Reactor, and Feign paths.

### Step 5: Report the review

Output the combination and modules inspected, upstream dependencies with evidence state, tests executed and remaining gaps, and violations with proposed fixes.

## Gotchas

- A module named in the README is not a completed capability — check the implementation, its registration, and its tests before counting it.
- An extension that re-pins a managed version breaks BOM ownership; flag it even when the build is green (fix belongs to `ddd4j-cloud-bom`).
- Reimplementing a missing Boot/ddd4j artifact inside ddd4j-cloud turns an upstream gap into a fork — the correct output is BLOCKED(upstream).
- Context/Tenant restoration verified only on the happy path is not coverage — the async, Reactor, and Feign terminal states are where restoration breaks.
- A stale CodeGraph index relative to the checkout SHA makes the boundary review describe a tree that no longer exists; refresh before reading.
- Old `cmpt` modules can survive as transitive references after the hard cut and resurrect deprecated naming in the module graph.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；所有示例均使用虚构的模块名与构件坐标。

## Quick Start

- "Use `$ddd4j-cloud-architecture` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-architecture` to review existing usage against the current source."
- "Use `$ddd4j-cloud-architecture` to return an implementation choice, evidence state, and remaining risk."

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
