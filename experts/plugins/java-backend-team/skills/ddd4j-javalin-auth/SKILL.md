---
name: ddd4j-javalin-auth
description: Use when integrating Sa-Token, Apache Shiro, or OIDC and Keycloak authentication with ddd4j-javalin routes, Subject providers, authorization, errors, and request cleanup. 中文触发词：认证、鉴权、Sa-Token、Shiro、OIDC、Keycloak、路由保护、401/403、Subject 清理。
license: Apache-2.0
---

# ddd4j-javalin Auth

## Overview

Covers Sa-Token, Shiro, OIDC/Keycloak, SubjectProvider, route protection, 401/403, and cleanup uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Integrating Sa-Token, Apache Shiro, or OIDC/Keycloak authentication with ddd4j-javalin routes on 6.7.x, 7.1.x, or 7.2.x.
- Implementing a `SubjectProvider` and mapping the framework identity to `AuthPrincipal` with explicit role/permission rules.
- Wiring route protection with explicit 401/403 semantics instead of framework defaults.
- Binding the request Subject at request start and cleaning it up on success, exception, and async terminal states.
- Choosing exactly one primary authentication framework per service and registering it as a lifecycle participant.

## When NOT to Use

Do not use this skill when:

- **Non-auth route behavior is the question (CORS, errors, validation, request limits, idempotency)** — use `ddd4j-javalin-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-web`.
- **The auth provider's lifecycle registration is the question** — use `ddd4j-javalin-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-runtime`.
- **The core `Subject`/`ThreadContext` SPI contracts are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Spring Security and Spring Boot wiring is the question** — use `ddd4j-boot-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-auth`. Quarkus: `ddd4j-quarkus-auth`.
- **A cross-capability review or release gate over auth hardening is needed** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **The project is a plain Javalin app without ddd4j** — do not use this skill; use `java-skills` instead, since `SubjectProvider` and the ddd4j Subject contracts do not exist there.

## Trigger Keywords

**English**: authentication, authorization, Sa-Token, Shiro, OIDC, Keycloak, route protection, subject cleanup

**中文**: 认证, 鉴权, Sa-Token, Shiro, OIDC, Keycloak, 路由保护, 401/403

## Core Scope

Sa-Token, Shiro, OIDC/Keycloak, SubjectProvider, route protection, 401/403, cleanup.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for authentication and Javalin adaptation.
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

Fix the maintenance line with `ddd4j-javalin-version-selection`, then locate the auth module, its `SubjectProvider` implementations, and the Keycloak/auth tests in the current checkout.

### Step 2: Select the framework

Compare Sa-Token, Shiro, and OIDC/Keycloak against the deployment model (single instance, cluster, existing IdP). Pick exactly one primary `SubjectProvider` per service and record why.

### Step 3: Wire route protection

Apply route-level protection with explicit 401/403 semantics, and map the framework identity to `AuthPrincipal` with explicit role/permission rules — not whatever the framework defaults to.

### Step 4: Clean up per request

Bind the Subject at request start and restore context on success, exception, and async completion. Confirm no token or cookie value can reach logs or error payloads.

### Step 5: Verify with real HTTP

Test anonymous, valid, expired, insufficient-role, and logout paths with real HTTP requests. Produce a report with the framework choice, registration points, evidence state per tier, and remaining risk.

## Gotchas

- Exactly one primary `SubjectProvider` per service — two frameworks registered at once (for example Sa-Token and OIDC) resolve silently by registration order, not by policy.
- Subject binding must be released on success, exception, and async paths; a pooled thread inherits the previous request's Subject and crosses user or tenant boundaries.
- An expired-token request returning 200 usually means the access manager was never registered — the auth module being on the classpath proves nothing about route protection.
- 401 versus 403 must be decided explicitly; framework defaults often collapse the two and hide misconfigured role mappings.
- Tokens, cookies, and OIDC secrets must be redacted in any evidence output — `Authorization` headers end up in logs by default in many handlers.
- Javalin 6 and Javalin 7 access-manager/route APIs differ — auth wiring copied between maintenance lines must be re-verified per line.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；认证示例仅使用脱敏的虚构数据，绝不输出真实令牌或 Cookie。

## Quick Start

- "Use `$ddd4j-javalin-auth` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-auth` to review existing usage against the current source."
- "Use `$ddd4j-javalin-auth` to return an implementation choice, evidence state, and remaining risk."

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
