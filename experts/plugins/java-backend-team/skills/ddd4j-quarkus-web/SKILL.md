---
name: ddd4j-quarkus-web
description: Use when building ddd4j Quarkus REST endpoints with request context, errors, authentication, validation, idempotency, CORS, limits, and readiness. 中文触发词：REST 接口、请求上下文、错误处理、认证、校验、幂等、CORS、就绪检查。
license: Apache-2.0
---

# ddd4j-quarkus Web

## Overview

Covers Quarkus REST/JAX-RS, Context, errors, Auth, Validation, idempotency, CORS, and Readiness uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Building REST endpoints on Quarkus REST/JAX-RS with ddd4j request `Context` bound at request start.
- Defining the HTTP contract: endpoints, status codes, payloads, and stable error responses.
- Configuring production controls: validation, authentication hooks, shared-CAS idempotency, explicit CORS, and request limits.
- Separating liveness from readiness backed by real dependencies.
- Testing HTTP normal, error, replay, and async paths with QuarkusTest in JVM and, where required, native mode.
- Reviewing an existing web layer's context handling and production controls on either line.

## When NOT to Use

Do not use this skill when:

- **Spring MVC / WebMvc endpoints are the target** — use `ddd4j-boot-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-web`; Spring interceptor semantics do not transfer to Quarkus REST filters.
- **Javalin HTTP endpoints are the target** — use `ddd4j-javalin-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-web`.
- **Gateway routing and cross-service web concerns in a Spring Cloud mesh** — use `ddd4j-cloud-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-web`.
- **The command/query contracts behind the endpoints are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Choosing or wiring the authentication mechanism itself** — use `ddd4j-quarkus-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-auth`.
- **The project is plain Quarkus REST without ddd4j** — generic Quarkus REST guidance applies; do not use the ddd4j Context model on a non-ddd4j stack.

## Trigger Keywords

**English**: REST endpoints, request context, error mapping, authentication hooks, validation, idempotency, CORS, readiness probe

**中文**: REST 接口, 请求上下文, 错误处理, 认证, 校验, 幂等, CORS, 就绪检查

## Core Scope

Quarkus REST/JAX-RS, Context, errors, Auth, Validation, idempotency, CORS, Readiness.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for web behavior and Quarkus adaptation.
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

Fix the line via `ddd4j-quarkus-version-selection`, then locate `ddd4j-quarkus-web`, `web-quarkus`, and the HTTP tests in that checkout. The REST idioms and context filters are per line.

### Step 2: Define the HTTP contract

Specify REST endpoints, status codes, payloads, and error responses, and bind request `Context` at request start using Quarkus REST filters/interceptors — with release on success, exception, and async completion.

### Step 3: Implement production controls

Configure validation, authentication hooks, shared-CAS idempotency, explicit CORS, and request limits, and separate liveness from readiness backed by real dependencies.

### Step 4: Test the HTTP paths

Run QuarkusTest HTTP suites covering normal, error, replay, and async paths, and confirm behavior holds in JVM mode and, where the deployment requires it, native mode.

### Step 5: Report

Produce a single report: endpoint inventory and contract coverage, configuration keys and override points, tests executed and evidence state per tier, and risks with proposed fixes and missing inputs.

## Gotchas

- Quarkus REST is not Spring MVC: Spring `HandlerInterceptor`/`ControllerAdvice` patterns do not transfer, and ported interceptors pass compile while binding at the wrong phase.
- Request `Context` bound in a filter must be released on error and async paths; worker-thread pools turn a success-only release into a cross-request data leak.
- Idempotency keys backed by shared CAS must actually be shared across instances — a local in-memory map passes single-node tests and duplicates under the second replica.
- Readiness backed by real dependencies differs from liveness; conflating them makes Kubernetes keep broken pods or restart healthy ones.
- Native image requires explicit registration for payload reflection; a green JVM-mode HTTP suite does not prove native-mode behavior.
- CORS and request limits must be explicit; a permissive dev-mode default that "just works" locally is a production risk, not a configuration.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；HTTP 请求与响应示例均为脱敏虚构数据。

## Quick Start

- "Use `$ddd4j-quarkus-web` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-web` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-web` to return an implementation choice, evidence state, and remaining risk."

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
