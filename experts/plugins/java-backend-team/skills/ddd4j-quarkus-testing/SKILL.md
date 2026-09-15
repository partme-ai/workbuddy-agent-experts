---
name: ddd4j-quarkus-testing
description: Use when testing ddd4j-quarkus with QuarkusTest, QuarkusTestResource, Arc validation, Docker conditions, Testcontainers, classloader boundaries, and native tests. 中文触发词：QuarkusTest、TestResource、Arc 校验、Docker 检测、ClassLoader、Native 测试、测试资源生命周期。
license: Apache-2.0
---

# ddd4j-quarkus Testing

## Overview

Covers QuarkusTest, TestResource, Arc, Docker, Testcontainers, ClassLoader, and native test uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Designing QuarkusTest suites with QuarkusTestResource lifecycle management for ddd4j-quarkus features.
- Planning Arc validation of bean scopes and registrations alongside behavioral suites.
- Running Testcontainers suites against real backends and recording Docker-unavailable runs as BLOCKED/SKIPPED.
- Deciding which contracts require native tests and running them in native mode.
- Recording evidence honestly: JVM versus native mode, source/behavior/container/CI/publish tiers kept separate.
- Diagnosing test failures caused by Quarkus's classloader boundaries or per-class TestResource lifecycle.

## When NOT to Use

Do not use this skill when:

- **The Spring Boot test strategy is the question (`@SpringBootTest`, MockMvc)** — use `ddd4j-boot-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-testing`; Spring test fixtures do not transfer to Quarkus.
- **Javalin testing is the target** — use `ddd4j-javalin-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-testing`.
- **Spring Cloud compatibility testing** — use `ddd4j-cloud-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-testing`.
- **Authoring the extension under test (Processor, BuildItems)** — use `ddd4j-quarkus-extension-authoring` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-extension-authoring`.
- **CI gates, publishing, or remote consumption after tests pass** — use `ddd4j-quarkus-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-release`; this skill should not be used to open release gates.
- **The project is plain Quarkus without ddd4j** — generic Quarkus/JUnit guidance applies; do not use the ddd4j evidence tiers on a non-ddd4j stack.

## Trigger Keywords

**English**: QuarkusTest, QuarkusTestResource, Arc validation, Docker condition, Testcontainers, classloader boundary, native test, evidence report

**中文**: QuarkusTest, TestResource, Arc 校验, Docker 检测, ClassLoader, Native 测试, 测试资源生命周期, 测试证据

## Core Scope

QuarkusTest, TestResource, Arc, Docker, Testcontainers, ClassLoader, native test.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for testing and Quarkus adaptation.
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

Fix the line via `ddd4j-quarkus-version-selection`, then locate the Quarkus test extensions and fixtures in that checkout. Test idioms and fixture layouts are per line.

### Step 2: Design the suite

Plan QuarkusTest suites with explicit QuarkusTestResource lifecycle management, Arc validation for scopes and registrations, and Testcontainers for every real backend the contract touches.

### Step 3: Execute

Run the JVM-mode suites covering HTTP, auth, data, MQ, and cache behaviors, and run native tests where the contract requires them — a native test is not optional evidence for native targets.

### Step 4: Record evidence honestly

Handle Docker availability across Quarkus's classloader boundaries and mark skips BLOCKED/SKIPPED, never PASS. Keep source, behavior, container, CI, and publish evidence separate.

### Step 5: Report

Produce a single report: suites executed with mode (JVM/native) and toolchain, pass/fail plus the BLOCKED/SKIPPED inventory, gaps against the feature matrix, and risks with proposed fixes and missing inputs.

## Gotchas

- TestResources are started per test class by default; `@QuarkusTestResource` lifecycle differs from Spring's one-per-context model, so resources assuming single startup leak state between classes.
- Quarkus runs tests across multiple classloaders — Docker and container-launcher detection code that works in a plain JVM `main()` can misreport inside a `@QuarkusTest` run.
- A native test is not equal to a JVM test; green JVM suites prove nothing about the native build, and skipped native runs must be reported BLOCKED/SKIPPED, never PASS.
- Arc validation happens at build time: an "unsatisfied dependency" at test startup is a discovery failure to fix in wiring, not a test bug to work around.
- Build-time configuration stays fixed even in tests — changing a `quarkus.*` build-time key via a test profile does not rebuild the world; use the profile that exists at build.
- Source, behavior, container, CI, and publish evidence are separate tiers; merging them (for example, "tests pass, so the artifact is consumable") overstates coverage.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；测试数据与报告均为脱敏虚构内容。

## Quick Start

- "Use `$ddd4j-quarkus-testing` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-testing` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-testing` to return an implementation choice, evidence state, and remaining risk."

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
