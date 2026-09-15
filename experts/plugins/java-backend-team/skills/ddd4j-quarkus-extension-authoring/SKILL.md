---
name: ddd4j-quarkus-extension-authoring
description: Use when creating or reviewing ddd4j Quarkus extensions with runtime and deployment modules, processors, BuildItems, recorders, configuration, bean registration, or native image support. 中文触发词：扩展开发、runtime/deployment 模块、Processor、BuildItem、Recorder、Bean 注册、配置映射、Native 支持。
license: Apache-2.0
---

# ddd4j-quarkus Extension Authoring

## Overview

Covers runtime/deployment, Processor, BuildItem, Recorder, configuration, bean registration, and native image uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Creating a new ddd4j Quarkus extension as a paired runtime and deployment module under `ddd4j-quarkus-extensions` / `extension-parent`.
- Writing or reviewing a `Processor` with explicit BuildItem consumption/production and `Recorder` calls.
- Registering beans or configuration mappings from an extension, without assuming a BOM import registers anything.
- Deciding which reflection/serialization registrations are required for native image support.
- Reviewing an existing extension's structure and registration points against the current line (3.3.x or 4.0.x).
- Explaining why an extension behaves differently between JVM and native, or dev and packaged, modes.

## When NOT to Use

Do not use this skill when:

- **Plain application-level CDI/Arc wiring of ddd4j SPIs (CommandBus, SubjectProvider) with no new extension** — use `ddd4j-quarkus-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-runtime`.
- **The SPI contracts the extension should expose are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Spring Boot starter/auto-configuration authoring is the goal** — use `ddd4j-boot-extensions` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-extensions`; do not copy BuildItem/Recorder patterns into a Spring build model.
- **The maintenance line is not yet chosen** — use `ddd4j-quarkus-version-selection` first. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-version-selection`.
- **Only the test strategy for the extension is requested** — use `ddd4j-quarkus-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-testing`.
- **The project is a plain Quarkus extension outside ddd4j** — generic Quarkus extension guidance applies; do not use the ddd4j extension-parent conventions on a non-ddd4j extension.

## Trigger Keywords

**English**: extension authoring, runtime deployment modules, Processor, BuildItem, Recorder, bean registration, configuration mapping, native image support

**中文**: 扩展开发, runtime/deployment 模块, Processor, BuildItem, Recorder, Bean 注册, 配置映射, Native 支持

## Core Scope

runtime/deployment, Processor, BuildItem, Recorder, configuration, bean registration, native image.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for extension authoring and Quarkus adaptation.
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

Fix the line via `ddd4j-quarkus-version-selection`, then locate `ddd4j-quarkus-extensions` and `extension-parent` in the checkout. The extension-parent conventions (module naming, processor wiring) are per line.

### Step 2: Structure the extension

Create the paired runtime and deployment modules and implement the `Processor` with explicit BuildItem consumption/production and `Recorder` calls. The deployment module holds all build steps; the runtime module holds the beans and SPI implementations.

### Step 3: Register beans and configuration

Define CDI scopes and configuration mappings in the runtime module and register beans via BuildItems — never assuming that a BOM import registers anything on its own.

### Step 4: Verify native boundaries

Confirm the reflection/serialization registrations needed for native image, and confirm Docker detection accounts for Quarkus's multiple classloaders. JVM-mode success proves neither.

### Step 5: Verify and report

Run the Arc/QuarkusTest suites plus a native test where the contract requires it, then produce a report with extension structure, registration points, evidence state, and remaining risk.

## Gotchas

- Quarkus extensions are a runtime/deployment module pair; the deployment module holds the build steps and is not on the runtime classpath, so a `Recorder` call path placed in the runtime module compiles but never runs at build time.
- Bean registration is build-time: without a BuildItem or a bean-defining annotation, a class present in source produces no bean, and there is no runtime component scan to save it.
- A BOM import registers nothing — the extension's build steps do the wiring; treating the BOM as the integration is the documented "BOM as runtime" anti-pattern.
- Native image requires explicit registration; reflection-based code that works in JVM mode can fail at native build if the reflection/serialization registrations were never added.
- Arc validates injection points at build time; an extension consuming an optional BuildItem must not assume the produced bean exists in every consuming application.
- Docker detection is special because Quarkus tests run across multiple classloaders — a check that works in a plain JVM `main()` can misreport inside a `@QuarkusTest` run.
- A native test is not equal to a JVM test; green JVM suites prove nothing about the native build, so native tests must be planned, not assumed.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；扩展示例仅使用虚构符号与脱敏配置。

## Quick Start

- "Use `$ddd4j-quarkus-extension-authoring` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-extension-authoring` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-extension-authoring` to return an implementation choice, evidence state, and remaining risk."

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
