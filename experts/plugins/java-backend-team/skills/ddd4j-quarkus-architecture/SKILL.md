---
name: ddd4j-quarkus-architecture
description: Use when designing or reviewing ddd4j-quarkus parent, BOM, extension-parent, auth, data, MQ, Web, cache, extension, or sample boundaries. 中文触发词：模块边界、parent、BOM、extension-parent、扩展边界、依赖方向、runtime/deployment 划分、边界审查。
license: Apache-2.0
---

# ddd4j-quarkus Architecture

## Overview

Covers parent, bom, dependencies, extension-parent, auth, data, mq, web, cache, extensions, and samples uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Designing or reviewing the ddd4j-quarkus module layout: parent, bom, dependencies, extension-parent, auth, data, mq, web, cache, extensions, samples.
- Deciding which module a new capability or sample belongs in, and which modules it may depend on.
- Checking that runtime and deployment modules are separated per the Quarkus build-time model on either line (3.3.x → Quarkus Platform 3.37.4 / JDK 17 / Maven 3; 4.0.x → Quarkus Platform 3.38.2 / JDK 21 / Maven 4).
- Producing a read-only boundary review with entry points, CDI registrations, and violations.
- Verifying that dependency direction between modules matches the current line's contract.
- Onboarding a developer to where each Quarkus adaptation lives in the ddd4j-quarkus tree.

## When NOT to Use

Do not use this skill when:

- **Authoring a new extension's Processor, BuildItems, or Recorder** — use `ddd4j-quarkus-extension-authoring` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-extension-authoring`.
- **Application-level CDI/Arc bean wiring or lifecycle** — use `ddd4j-quarkus-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-runtime`.
- **The maintenance line itself is not yet chosen** — use `ddd4j-quarkus-version-selection` first. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-version-selection`.
- **The domain/SPI contracts behind the modules are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Spring Boot module boundaries are the question** — use `ddd4j-boot-architecture` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-architecture`.
- **The codebase is a plain Quarkus project without ddd4j** — generic Java and Quarkus skills apply; do not use the ddd4j module map on a non-ddd4j stack.

## Trigger Keywords

**English**: module boundaries, parent BOM, extension-parent, dependency direction, runtime deployment split, boundary review, module map, sample placement

**中文**: 模块边界, parent, BOM, extension-parent, 依赖方向, runtime/deployment 划分, 边界审查, 模块划分

## Core Scope

parent, bom, dependencies, extension-parent, auth, data, mq, web, cache, extensions, samples.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for architecture and Quarkus adaptation.
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

Fix the line (3.3.x or 4.0.x) via `ddd4j-quarkus-version-selection` first, then confirm the branch, SHA, and CodeGraph health of the checkout. A review against a stale checkout maps modules that no longer exist.

### Step 2: Map the modules

Enumerate parent, bom, dependencies, extension-parent, auth, data, mq, web, cache, extensions, and samples, and separate runtime from deployment modules per the Quarkus build-time model. Record entry points for each.

### Step 3: Verify CDI wiring

Check bean scopes, qualifiers, and BuildItem/Recorder usage without projecting the Spring model onto Arc, and confirm request Context binding and cleanup across startup/shutdown and native boundaries.

### Step 4: Validate behavior

Run Arc/QuarkusTest suites for the target modules and confirm BOM imports do not masquerade as registered beans. Presence of a BOM import is not evidence of a working integration.

### Step 5: Report the boundary review

Produce a single report: line and modules inspected with entry points, CDI registrations and scopes with lifecycle owners, tests executed and evidence state per tier, and violations and risks with proposed fixes.

## Gotchas

- Quarkus extensions are a runtime/deployment module pair; the deployment module holds the build steps and is not on the runtime classpath, so a review that reads only the runtime side misses half the wiring.
- A BOM import does not mean the runtime bean is assembled — build items and recorders do the wiring; "bom/ is imported by this module" is not evidence of integration.
- CDI bean discovery in Quarkus is build-time: Arc validates injection points during the build, and a class present in source but never discovered produces no bean.
- Reading `4.0.x` as Quarkus Platform 4 corrupts every boundary conclusion — both lines sit on Platform 3.x (3.37.4 / 3.38.2); the BOM is the authority.
- Spring assembly intuition (component scan, auto-configuration) must not be projected onto Arc; the Quarkus build-time/CDI model has no counterpart to `@ComponentScan`.
- Request Context that is bound but never released fails differently at native boundaries than in JVM mode; startup/shutdown ownership must be explicit per module.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；审查结果仅引用脱敏的模块与代码路径。

## Quick Start

- "Use `$ddd4j-quarkus-architecture` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-architecture` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-architecture` to return an implementation choice, evidence state, and remaining risk."

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
