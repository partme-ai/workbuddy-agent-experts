---
name: ddd4j-javalin-version-selection
description: Use when choosing a ddd4j-javalin maintenance line based on Javalin, ddd4j, JDK, Maven, and POM model constraints. 中文触发词：版本选择、维护线、兼容矩阵、JDK 对应、Maven 版本、POM 模型、升级路径。
license: Apache-2.0
---

# ddd4j-javalin Version Selection

## Overview

Covers uniformly: 6.7.x→Javalin 6.7/ddd4j 1/JDK17/Maven3; 7.1.x→Javalin 7.1/ddd4j 2/JDK17/Maven3; 7.2.x→Javalin 7.2/ddd4j 3/JDK21/Maven4. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Starting work on any `ddd4j-javalin` branch and needing to fix the maintenance line tuple before quoting any API — 6.7.x → Javalin 6.7/ddd4j 1/JDK 17/Maven 3; 7.1.x → Javalin 7.1/ddd4j 2/JDK 17/Maven 3; 7.2.x → Javalin 7.2/ddd4j 3/JDK 21/Maven 4.
- The checkout's POM model, Maven Wrapper, or JDK disagrees with the branch name, and you must decide which contract is authoritative.
- Verifying a line's toolchain with `BuildLineContractTest`, the root POM, and `./mvnw -version` before implementing or reviewing.
- Planning a migration or compatibility comparison between maintenance lines (for example 6.7.x → 7.2.x).
- Deciding whether an API seen on one line can be used on another line without per-line re-verification.

## When NOT to Use

Do not use this skill when:

- **The maintenance line is already confirmed and one capability must be implemented or reviewed** — use the matching capability skill such as `ddd4j-javalin-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-runtime`.
- **A whole-service cross-capability review, plan approval, or release gate is needed** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **Core domain or SPI contracts (`AggregateRoot`, `Command`, `Repository`, `Subject`) are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Spring Boot ddd4j version selection is the question** — use `ddd4j-boot-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-version-selection`.
- **Quarkus ddd4j version selection is the question** — use `ddd4j-quarkus-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-version-selection`.
- **Spring Cloud ddd4j version selection is the question** — use `ddd4j-cloud-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-version-selection`.
- **The project is a plain Javalin or generic Java codebase without ddd4j** — do not use this skill; use `java-skills` instead, since no ddd4j maintenance-line contract applies.

## Trigger Keywords

**English**: version selection, maintenance line, compatibility matrix, JDK mapping, Maven version, POM model, upgrade path

**中文**: 版本选择, 维护线, 兼容矩阵, JDK 对应, Maven 版本, POM 模型, 升级路径

## Core Scope

6.7.x→Javalin 6.7/ddd4j 1/JDK17/Maven3; 7.1.x→Javalin 7.1/ddd4j 2/JDK17/Maven3; 7.2.x→Javalin 7.2/ddd4j 3/JDK21/Maven4.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for version selection and Javalin adaptation.
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

### Step 1: Select the version line

Gather the target Javalin version, JDK, and Maven from the project, then match them against the three line tuples. Verify the match with `BuildLineContractTest` and the current POMs, never the branch name alone.

### Step 2: Locate feature modules and entry points

Enumerate the line's feature modules, entry points, and providers, including the POM layout contract (Maven 3 `<modules>` versus Maven 4 `<subprojects>`). This determines where implementation and configuration belong on that line.

### Step 3: Compare implementations and overrides

Read the current branch source and compare configuration, overrides, and degradation behavior between candidate lines. Flag anything that is aligned by behavior only — Javalin 6 versus 7 differences must be adapted, not copied.

### Step 4: Verify contract evidence

Build and run the line's behavior tests, and check CI status for the final SHA. Consume artifacts with an isolated clean cache where required, and keep source, test, CI, and publish evidence separate.

### Step 5: Report the line and remaining risk

Output the selected tuple (Javalin, ddd4j, JDK, Maven/POM), the verification commands with evidence state per tier, incompatible and unverified items, and `missing:` entries for anything not supplied.

## Gotchas

- 7.1.x's formal contract is Maven 3 — Maven 4 belongs to 7.2.x only, even when a local build happens to succeed with the wrong toolchain.
- Javalin 6 and Javalin 7 APIs differ — code must not be copied mechanically between maintenance lines.
- The branch name is a hypothesis, not evidence; the root POM model, Maven Wrapper, and `BuildLineContractTest` decide the actual line.
- A class existing in source does not prove the capability works — registration and behavior evidence are separate gates.
- A container starting is not behavior passing; Testcontainers being up means nothing until a contract test asserts against it.
- Evidence tiers must stay separate — source review, tests, CI, and publication are four different states, and one never implies another.
- A JDK mismatch (for example JDK 17 on 7.2.x, which requires JDK 21) may surface only at build or runtime; verify `java -version` against the tuple instead of assuming.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；版本矩阵示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-version-selection` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-version-selection` to review existing usage against the current source."
- "Use `$ddd4j-javalin-version-selection` to return an implementation choice, evidence state, and remaining risk."

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
