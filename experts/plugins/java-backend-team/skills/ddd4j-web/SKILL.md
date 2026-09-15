---
name: ddd4j-web
description: Use when implementing or reviewing ddd4j HTTP contracts across Spring MVC, WebFlux, Javalin, Quarkus REST, Micronaut, Vert.x, Helidon, or Dropwizard, including context, errors, validation, authentication, idempotency, CORS, limits, and readiness. 中文触发词：HTTP 契约、统一响应、错误处理、上下文透传、认证、幂等、CORS、就绪检查、参数校验。
license: Apache-2.0
---

# ddd4j Web

## Overview

`ddd4j-web-core` defines the cross-runtime behavior. Each adapter implements the same HTTP contract. Framework APIs may differ, but response, context, and security behavior must remain consistent.

## When to Use

- Implementing or porting the ddd4j HTTP contract across the adapters: `webmvc`, `webflux`, `javalin`, `quarkus`, `micronaut`, `vertx`, `helidon`, `dropwizard`.
- Binding Request/Trace/Tenant/Subject context at the entry point and cleaning up on success, exception, and async completion.
- Mapping failures to the stable error contract (400, 401, 403, 404, 409, 415, 422, 429, 500) without leaking internal stack traces.
- Using the validation constraints — `AllowableValues(allows, nullable)`, `PhoneNumber(lang)`, `NumberValue(regex)`, `StringDateValue(pattern)` — and wiring the Jakarta/Javax validation dependency per line.
- Configuring production controls: idempotency scope, CORS allowlist, request-size/timeout/rate limits.
- Separating liveness from readiness, with readiness aggregating real dependencies (DB, MQ, Auth, Outbox).
- Aligning runtimes with `web-testkit` endpoints and assertions.

## When NOT to Use

Do not use this skill when:

- **The authentication chain itself is the question** (SubjectProvider, tokens, roles) — use `ddd4j-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-auth`; this skill consumes the Subject and owns only the HTTP contract around it.
- **Idempotency CAS storage or TTL semantics are the question** — use `ddd4j-cache` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cache`; the web layer chooses the scope, the cache layer implements it.
- **Framework registration and lifecycle wiring are the question** — use `ddd4j-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-runtime`.
- **A request treats HTTP 200 as proof of business correctness, or asks to hardcode `READY`** — do not use this skill to endorse that; both are explicit anti-patterns here.
- **Generic Spring MVC controller advice or Javalin handler style with no ddd4j contract involved** — use the framework's own skills; cross-runtime contract consistency is ddd4j-web's territory only.

## Trigger Keywords

**English**: HTTP contract, unified response, error mapping, context propagation, authentication, idempotency, CORS allowlist, readiness probe

**中文**: HTTP 契约, 统一响应, 错误处理, 上下文透传, 认证, 幂等, CORS 白名单, 就绪检查

## Runtimes and Capabilities

Spring MVC, WebFlux, Javalin, Quarkus REST, Micronaut, Vert.x, Helidon, Dropwizard — uniformly covering response / errors, Request / Trace / Tenant context, authentication, idempotency, CORS, request size, async timeout, liveness / readiness, and validation.

## Core Rules

1. Bind context at request start; clean up on success, exception, and async completion.
2. Authentication failures, authorization failures, validation failures, and system errors use stable status codes and payloads.
3. Idempotency distinguishes closed, single-instance, and shared CAS scopes.
4. CORS in production uses an explicit allowlist.
5. Liveness and readiness are separate; readiness aggregates real dependencies.
6. The Testkit contract is the cross-runtime alignment evidence.

## Capability Boundaries

### ✅ Strong At

- A unified contract across multiple web runtimes.
- Context, errors, authentication, idempotency, CORS, and readiness.
- The four ddd4j validation constraints.
- HTTP contract testing.

### ⚠️ Needs Input

- Target runtime and maintenance line.
- Public endpoints and error contract.
- Deployment, proxy, and authentication mode.

### ❌ Out of Scope

- Treating HTTP 200 as proof of business correctness.
- Hardcoding `READY`.
- Leaking framework Context into the domain layer.

## Workflow

### Step 1: Choose the runtime and read the matching adapter

Pick the adapter (`webmvc`, `webflux`, `javalin`, `quarkus`, `micronaut`, `vertx`, `helidon`, `dropwizard`) and read its actual API and tests on the target branch — the contract is shared, the idioms are not.

### Step 2: Define behavior with the web-testkit contract

Write the expected paths and payloads against `web-testkit` first: unified response shape, error mapping per status family, context headers. The testkit contract is the cross-runtime alignment evidence.

### Step 3: Implement binding, auth, handling, and cleanup

Bind Request/Trace/Tenant/Subject at the entry point; implement authentication checks, handler dispatch, and exception translation — and clean up the context on success, exception, and async completion.

### Step 4: Configure the production controls

Set CORS as an explicit allowlist (origin, credentials, headers, methods), idempotency scope (closed / single-instance / shared CAS), request size, async timeout, and rate limits; separate liveness from readiness, with readiness aggregating DB, MQ, Auth, and Outbox participants.

### Step 5: Run normal, error, replay, and thread-reuse tests

Execute the testkit suite: normal requests, each error class, idempotency replay, and same-thread reuse after a request ends — context residue and error-shape drift show up there, not in happy paths.

## Gotchas

- Context cleanup wired on the success path only — exception and async-completion paths leave the previous request's Subject/tenant bound, and pooled threads surface it as cross-user data leakage.
- Hardcoded `READY` that ignores real participants — the process reports healthy while the database, MQ, or Outbox is down; readiness must aggregate required dependencies, liveness stays process-only.
- Permissive CORS surviving from development into production — `*` origins with credentials enabled is a standing breach; production uses an explicit allowlist.
- Local idempotency impersonating cluster scope — a single-instance map passes every one-pod test and duplicates under the load balancer; production shared CAS must be a separate, tested configuration.
- Adapter drift — the contract implemented correctly on one runtime and ported by memory to another; only `web-testkit` alignment proves the behaviors are the same.
- The unified error payload swallowing the cause or leaking internal stack traces — both defects violate the contract: the cause must be preserved internally, the trace must never be exposed.
- Validation null semantics assumed uniform — `NumberValue`/`PhoneNumber` null behavior requires `NotNull` plus tests, `StringDateValue` passes empty strings while strictly parsing dates, and 3.0.x uses `jakarta.validation` while older lines differ.

## Deep Reference

- [Runtime Matrix](references/runtime-matrix.md)
- [Context and Errors](references/context-and-errors.md)
- [Validation](references/validation.md)
- [Idempotency, CORS, Readiness](references/production-controls.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never log `Authorization`, `Cookie`, full request bodies, or private fields. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；请求头与错误示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-web` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-web` to review existing usage against the current source."
- "Use `$ddd4j-web` to return an implementation choice, evidence state, and remaining risk."

## Audience and Customization

- Developers: provide the target maintenance line, POM, capabilities, and acceptance behavior.
- Architects: specify a read-only boundary, compatibility, or migration review.
- Testers / release engineers: specify the required evidence levels; do not auto-expand to release or production operations.

Customize the target framework, allowed implementations, excluded modules, compatibility requirements, and evidence level. When input is insufficient, give a tentative verdict first, then list `missing: specific item; how to provide: path or configuration`.

## FAQ

1. **Are skills organized by Maven artifact?** No — by the user-facing capability domain.
2. **Can I copy another maintenance line directly?** No — verify the version and source first.
3. **Does a class existing in source prove the capability works?** No — registration and behavior evidence are also required.
4. **How do I report tests that did not run?** Mark `NOT RUN` or `BLOCKED`.
5. **Can the skill commit or release automatically?** Only after explicit user authorization.
6. **What if the implementation is missing?** Describe the missing module or evidence; do not invent APIs.
