---
name: ddd4j-javalin-web
description: Use when building ddd4j-javalin routes, request context, errors, CORS, authentication, validation, idempotency, request limits, async timeouts, or health endpoints. 中文触发词：路由、Context、错误处理、CORS、校验、幂等、限流、健康检查。
license: Apache-2.0
---

# ddd4j-javalin Web

## Overview

Covers routes, Request/Trace/Tenant Context, errors, CORS, auth, validation, idempotency, limits, async, and health uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Building routes, error/exception mapping, validation, request limits, and async timeouts on Javalin for 6.7.x, 7.1.x, or 7.2.x.
- Binding Request/Trace/Tenant Context at request start and restoring it on success, exception, and async completion.
- Configuring CORS explicitly — origins, credentials, headers, and methods — for a production deployment.
- Implementing idempotency for write endpoints, including the shared-CAS requirement for multi-instance production.
- Providing distinct liveness and readiness endpoints backed by real dependency state.

## When NOT to Use

Do not use this skill when:

- **The authentication framework, token validation, or role mapping is the question** — use `ddd4j-javalin-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-auth`.
- **Where the health state comes from (participant lifecycle, readiness aggregation) is the question** — use `ddd4j-javalin-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-runtime`.
- **The core Request/Context/Subject SPI types are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **A cross-capability review or release gate is needed** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **Spring Boot, Quarkus, or Spring Cloud web wiring is the question** — use `ddd4j-boot-web`, `ddd4j-quarkus-web`, or `ddd4j-cloud-web` instead, for example Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-web`.
- **The project is a plain Javalin app without ddd4j** — do not use this skill; use `java-skills` instead, since the Request/Trace/Tenant Context contracts do not exist there.

## Trigger Keywords

**English**: routes, request context, error handling, CORS, validation, idempotency, request limits, health endpoints

**中文**: 路由, Context, 错误处理, CORS, 校验, 幂等, 限流, 健康检查

## Core Scope

routes, Request/Trace/Tenant Context, errors, CORS, auth, validation, idempotency, limits, async, health.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for web behavior and Javalin adaptation.
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

Fix the maintenance line with `ddd4j-javalin-version-selection`, then locate the web module, the web-testkit paths, and the HTTP contract tests in the current checkout.

### Step 2: Define the HTTP contract

Specify routes, status codes, payloads, and error responses via the web-testkit paths before implementing handlers. Confirm Request/Trace/Tenant Context binding happens at request start.

### Step 3: Implement production controls

Configure CORS origins, credentials, headers, and methods explicitly — never a wildcard default. Configure validation, idempotency (shared CAS for multi-instance production), request limits, and async timeouts.

### Step 4: Clean up and report health

Restore Context/Subject on success, exception, and async completion. Provide distinct liveness (process-only) and readiness endpoints backed by real dependency state.

### Step 5: Verify with contract tests

Run normal, error, replay, and async HTTP contract tests against the implemented behavior. Produce a report with contract coverage, evidence state per tier, and remaining risk.

## Gotchas

- `anyHost()` must not survive into production — CORS is explicit origins, credentials, headers, and methods, or it is a finding.
- Caffeine-backed idempotency is a single-instance fallback only; multi-instance production needs shared CAS, and the replay path must be tested against the shared backend.
- A smoke test that returns 200 does not prove routing, auth, or DB behavior — contract tests must assert status, payload, and side effects.
- Context restoration must cover success, exception, and async completion; the exception path is the one load testing typically surfaces on pooled threads.
- Liveness must remain process-only while readiness aggregates real dependencies (DB, MQ, OIDC, Outbox) — swapping them makes the platform restart the pod on every downstream outage.
- Javalin 6 and Javalin 7 handler/exception APIs differ (`unsafe.routes` is relevant on Javalin 7); route code copied between maintenance lines must be re-verified per line.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；HTTP 示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-web` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-web` to review existing usage against the current source."
- "Use `$ddd4j-javalin-web` to return an implementation choice, evidence state, and remaining risk."

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
