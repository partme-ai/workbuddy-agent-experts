---
name: ddd4j-quarkus-auth
description: Use when integrating JWT, OIDC, Shiro, or Sa-Token authentication with ddd4j-quarkus Subject providers, roles, permissions, request scope, and errors. 中文触发词：认证集成、JWT、OIDC、Shiro、Sa-Token、SubjectProvider、角色权限、请求作用域、令牌过期。
license: Apache-2.0
---

# ddd4j-quarkus Auth

## Overview

Covers JWT, OIDC, Shiro, Sa-Token, SubjectProvider, RolesAllowed, and request scope uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Choosing among JWT, OIDC, Shiro, and Sa-Token for a ddd4j-quarkus service against its deployment model.
- Registering exactly one primary `SubjectProvider` via CDI and mapping identities to `AuthPrincipal` with explicit role/permission rules.
- Applying `RolesAllowed` and mapping security exceptions to stable error responses.
- Binding the Subject at request start and restoring it on success, exception, and async completion paths.
- Verifying anonymous, valid, expired, and insufficient-role paths with QuarkusTest on either line.
- Reviewing existing auth wiring (duplicate providers, missing expiry tests, printed secrets) on the 3.3.x or 4.0.x line.

## When NOT to Use

Do not use this skill when:

- **Generic CDI bean wiring with no auth semantics (producers, scopes, observers)** — use `ddd4j-quarkus-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-runtime`.
- **The Subject/Context SPI contract itself is the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Spring Boot authentication wiring** — use `ddd4j-boot-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-auth`; Spring Security semantics do not transfer to Quarkus.
- **Javalin authentication wiring** — use `ddd4j-javalin-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-auth`.
- **Cross-service subject/tenant propagation in a Spring Cloud mesh** — use `ddd4j-cloud-context` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-context`.
- **The project is plain Quarkus without ddd4j** — generic Quarkus security guidance applies; do not use the ddd4j SubjectProvider model on a non-ddd4j stack.
- **Identity-provider operations are the task (Keycloak realm setup, token rotation)** — that is provider administration; this skill wires the application side and should not manage provider infrastructure.

## Trigger Keywords

**English**: authentication integration, JWT, OIDC, Shiro, Sa-Token, SubjectProvider, role permission mapping, request scope, token expiry

**中文**: 认证集成, JWT, OIDC, Shiro, Sa-Token, SubjectProvider, 角色权限, 请求作用域, 令牌过期

## Core Scope

JWT, OIDC, Shiro, Sa-Token, SubjectProvider, RolesAllowed, request scope.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for authentication and Quarkus adaptation.
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

Fix the line via `ddd4j-quarkus-version-selection`, then locate `ddd4j-quarkus-auth` and the authentication tests in that checkout. The supported mechanisms and registration idioms are per line.

### Step 2: Select the mechanism

Compare JWT, OIDC, Shiro, and Sa-Token against the deployment model (token validation location, identity provider, native-image needs), then register exactly one primary `SubjectProvider` via CDI.

### Step 3: Wire authorization

Map identities to `AuthPrincipal` with explicit role/permission rules, apply `RolesAllowed` on the endpoints that need them, and map security exceptions to stable error responses rather than leaking provider internals.

### Step 4: Manage request scope

Bind the Subject at request start and restore context on success, exception, and async completion; confirm the behavior holds under native image boundaries where the deployment requires it.

### Step 5: Verify

Run QuarkusTest suites covering anonymous, valid, expired, and insufficient-role paths, then produce a report with mechanism choice, registration points, evidence state, and remaining risk.

## Gotchas

- Registering a second `SubjectProvider` is an ambiguous-resolution build failure in Arc, not a "last one wins" — exactly one primary provider must exist.
- Spring Security semantics (`SecurityContextHolder`, filter chains) do not transfer; Quarkus uses its own identity providers and `RolesAllowed`, so ported configs pass compile and fail authorization.
- The Subject bound at request start must be released on the exception and async-completion paths too; a success-only release lets the next request on the pooled thread inherit the previous user's identity.
- Expired-token and insufficient-role behavior must be asserted by dedicated tests — a suite that only covers valid tokens stays green while expiry handling is broken.
- OIDC and token configuration can contain secrets; reports must redact them — printing the resolved configuration leaks credentials.
- Native image requires explicit registration for token parsers that use reflection; a green JVM-mode auth suite does not prove native-mode behavior.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；认证示例中的令牌与角色均为脱敏虚构数据。

## Quick Start

- "Use `$ddd4j-quarkus-auth` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-auth` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-auth` to return an implementation choice, evidence state, and remaining risk."

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
