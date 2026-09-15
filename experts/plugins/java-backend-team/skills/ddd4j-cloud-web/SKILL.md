---
name: ddd4j-cloud-web
description: Use when building ddd4j-cloud Spring MVC or WebFlux services with internationalized responses, errors, context, tenant, authentication, validation, and readiness. 中文触发词：国际化响应、统一错误、认证、校验、就绪检查、健康检查。
license: Apache-2.0
---

# ddd4j-cloud Web

## Overview

Covers MVC, WebFlux, i18n responses, errors, context, tenant, auth, validation, and readiness uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Building HTTP endpoints with the webmvc/webflux extensions in a ddd4j-cloud service.
- Designing unified error responses and internationalized response messages.
- Binding context and tenant at request start and wiring authentication to `SubjectProvider`.
- Defining validation constraints and their mapping into the error contract.
- Implementing readiness that aggregates real dependencies (database, Nacos, Sentinel) with liveness kept distinct.
- Running HTTP contract tests covering normal, error, i18n, replay, and async paths.

## When NOT to Use

Do not use this skill when:

- **Context propagation mechanics between threads are the question** — use `ddd4j-cloud-context` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-context`.
- **Tenant isolation rules are the question** — use `ddd4j-cloud-tenant` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-tenant`.
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-web`.
- **The runtime is Javalin or Quarkus** — use `ddd4j-javalin-web` or `ddd4j-quarkus-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-web` (or `--skill ddd4j-quarkus-web`).
- **Nacos/Sentinel/monitoring configuration itself is the question** — use `ddd4j-cloud-observability` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-observability` (readiness aggregation of those dependencies stays here).
- **Generic Spring MVC/WebFlux without ddd4j** — do not use this skill; apply generic `spring-cloud` / Java guidance instead (no install command).

## Trigger Keywords

**English**: unified error response, i18n messages, request validation, authentication, readiness, liveness, HTTP contract

**中文**: 国际化响应, 统一错误, 认证, 校验, 就绪检查, 健康检查

## Core Scope

MVC, WebFlux, i18n response, errors, context, tenant, auth, validation, readiness.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for web behavior and Spring Cloud integration.
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

Run `ddd4j-cloud-version-selection` to fix the combination, then locate the webmvc/webflux extensions and their tests on the confirmed branch and SHA.

### Step 2: Define the HTTP contract

Specify endpoints, status codes, payloads, and error responses. Plan internationalized response messages and validation constraints, and how validation failures map into the error contract.

### Step 3: Wire context and tenant

Bind context and tenant at request start and restore them on sync, async, Reactor, and Feign terminal states. Wire authentication to `SubjectProvider`.

### Step 4: Implement readiness

Aggregate readiness from real dependencies — database, Nacos, Sentinel as applicable — and keep liveness distinct. Never hardcode READY.

### Step 5: Verify the contract

Run HTTP contract tests covering normal, error, i18n, replay, and async paths, then report contract coverage, evidence state, and remaining risk.

## Gotchas

- Readiness must aggregate real dependencies: hardcoding READY (or reusing the liveness probe for readiness) hides a down Nacos or Sentinel and keeps traffic flowing into a service that cannot serve.
- WebFlux runs handlers on event-loop threads — one blocking call stalls every request on that loop, and the `ThreadLocal`-bound context does not follow Reactor operators without explicit propagation.
- Async or deferred controller results complete on another thread — i18n locale, context, and tenant must be captured before the handoff, not read when the response is written.
- The MVC and WebFlux extensions are not interchangeable mid-line: mixing both stacks in one service is an unverified configuration until proven on the line.
- Validation errors must surface through the unified error contract; a raw `BindException` stack trace escaping to clients breaks the response contract and leaks internals.
- A green start is not readiness evidence — probe behavior must be tested per dependency state (dependency down → not ready), not just at boot.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；请求与响应示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-cloud-web` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-web` to review existing usage against the current source."
- "Use `$ddd4j-cloud-web` to return an implementation choice, evidence state, and remaining risk."

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
