---
name: ddd4j-javalin-testing
description: Use when testing ddd4j-javalin across Javalin 6 and 7 with HTTP contracts, Keycloak, PostgreSQL, MQ brokers, Testcontainers, Docker conditions, ports, and lifecycle tests. 中文触发词：测试、Testcontainers、Docker、端口绑定、生命周期测试、HTTP 契约测试、证据分级。
license: Apache-2.0
---

# ddd4j-javalin Testing

## Overview

Covers Javalin 6/7 HTTP, Keycloak, PostgreSQL, MQ, Testcontainers, Docker, port 0, and lifecycle uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Building the test suite for a ddd4j-javalin service on 6.7.x, 7.1.x, or 7.2.x: HTTP contract tests via web-testkit paths, plus Keycloak, PostgreSQL, and MQ broker round-trips via Testcontainers.
- Writing lifecycle tests: startup success, partial failure with rollback, restart, and repeated starts without shutdown-hook accumulation.
- Deciding evidence honestly: Docker-unavailable, skipped containers, and zero-test runs must be reported `BLOCKED`/`SKIPPED`, never `PASS`.
- Verifying the same behavior across Javalin 6 and 7 maintenance lines, each on its own toolchain.
- Keeping configuration, behavior, container, CI, and publish evidence in separate tiers when reporting suite results.

## When NOT to Use

Do not use this skill when:

- **The behavior under test must first be implemented** — use the matching capability skill such as `ddd4j-javalin-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-web`.
- **CI gating, publishing, or remote-consumer validation after tests pass is the question** — use `ddd4j-javalin-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-release`.
- **Plan approval, cross-capability gates, or production-acceptance orchestration is the question** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **The maintenance line itself must be chosen or verified** — use `ddd4j-javalin-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-version-selection`.
- **Spring Boot, Quarkus, or Spring Cloud test conventions are the question** — use `ddd4j-boot-testing`, `ddd4j-quarkus-testing`, or `ddd4j-cloud-testing` instead, for example Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-testing`.
- **The project is a plain JUnit/Javalin codebase without ddd4j** — do not use this skill; use `java-skills` instead, since the ddd4j testkits and lifecycle contracts do not exist there.

## Trigger Keywords

**English**: testing, Testcontainers, Docker, port binding, lifecycle tests, HTTP contract tests, evidence grading

**中文**: 测试, Testcontainers, Docker, 端口绑定, 生命周期测试, HTTP 契约测试, 证据分级

## Core Scope

Javalin 6/7 HTTP, Keycloak, PostgreSQL, MQ, Testcontainers, Docker, port 0, lifecycle.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for testing and Javalin adaptation.
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

Fix the maintenance line with `ddd4j-javalin-version-selection`, then locate `ddd4j-javalin-testcontainers` and the web, auth, and data test suites in the current checkout.

### Step 2: Design the suite

Plan HTTP contract tests against the web-testkit paths, and Keycloak, PostgreSQL, and MQ broker round-trips via Testcontainers. Bind port 0 so parallel CI runs and containerized executions never fight over fixed ports.

### Step 3: Execute the suites

Run lifecycle tests covering startup success, partial failure, restart, and repeated starts without hook accumulation, then the behavior suites for HTTP, auth, data, and MQ. A container starting is not a pass — assertions must target the behavior.

### Step 4: Record evidence honestly

Mark Docker-unavailable or skipped container runs `BLOCKED`/`SKIPPED` — never `PASS`. Keep configuration, behavior, container, CI, and publish evidence as separate tiers that never stand in for each other.

### Step 5: Report the suite state

Produce a single report: suites executed with the line and toolchain, pass/fail plus the `BLOCKED`/`SKIPPED` inventory, gaps against the feature matrix, and risks with proposed fixes and missing inputs.

## Gotchas

- A smoke test that returns 200 does not prove routing, auth, or DB behavior — contract tests must assert status, payload, and side effects.
- Docker unavailable, zero tests executed, or skipped containers must be reported `BLOCKED`/`SKIPPED` — translating any of them into `PASS` is the core evidence violation this skill exists to prevent.
- Port 0 binding is mandatory; a hardcoded port breaks parallel CI and containerized runs in ways that look like flaky tests rather than configuration defects.
- A shutdown hook registered per start accumulates across embedded tests and repeated starts — the repeated-start test must assert no stale hooks remain.
- Javalin 6 and Javalin 7 testkit/route APIs differ; a suite copied across maintenance lines must actually run on both lines' toolchains, not just compile.
- A Keycloak or broker container becoming ready is not behavior passing — the token/role or publish/consume contract test must execute against it.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；测试报告示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-testing` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-testing` to review existing usage against the current source."
- "Use `$ddd4j-javalin-testing` to return an implementation choice, evidence state, and remaining risk."

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
