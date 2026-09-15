---
name: ddd4j-cloud-feign
description: Use when configuring ddd4j-cloud Feign interceptors, context and tenant headers, error decoder factories, retries, request cleanup, and service-to-service contracts. 中文触发词：服务调用、拦截器、Header 传播、错误解码、重试、请求清理。
license: Apache-2.0
---

# ddd4j-cloud Feign

## Overview

Covers request interceptors, context/tenant headers, error decoders, retries, and cleanup uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Registering Feign request interceptors that propagate context and tenant headers between services.
- Defining the header allowlist and preventing credential leakage to downstream services.
- Installing the error decoder factory that maps remote errors to the stable contract.
- Configuring retries with backoff and idempotency guarantees.
- Verifying request-scoped cleanup after each Feign call, including exception, timeout, and retry terminal states.
- Proving service-to-service contracts with real round-trips.

## When NOT to Use

Do not use this skill when:

- **How context is bound and restored inside this service is the question** — use `ddd4j-cloud-context` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-context`.
- **Async messaging fits better than synchronous calls** — do not force Feign; use `ddd4j-cloud-stream` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-stream`.
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-web`.
- **The runtime is Javalin or Quarkus** — use the matching `ddd4j-javalin-*` / `ddd4j-quarkus-*` skill instead (for example `ddd4j-javalin-web`, `ddd4j-quarkus-runtime`).
- **Generic Spring Cloud OpenFeign without ddd4j** — apply generic `spring-cloud` guidance instead (no install command); do not use this skill.
- **The remote service's own API contract is the question** — that belongs to the owning service, not to this skill's plumbing.

## Trigger Keywords

**English**: service call, Feign interceptor, header propagation, error decoder, retry policy, request cleanup, header allowlist

**中文**: 服务调用, 拦截器, Header 传播, 错误解码, 重试, 请求清理

## Core Scope

Request interceptor, context/tenant header, error decoder, retry, cleanup.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for Feign and Spring Cloud integration.
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

Run `ddd4j-cloud-version-selection` to fix the combination, then locate the Feign extension source and tests on the confirmed branch and SHA.

### Step 2: Wire interceptors

Register request interceptors that propagate context and tenant headers, define the header allowlist explicitly, and confirm no credentials leak to downstream services.

### Step 3: Configure errors and retries

Install the error decoder factory that maps remote errors to the stable contract, and configure retries with backoff plus explicit idempotency guarantees per endpoint.

### Step 4: Manage request cleanup

Confirm request-scoped resources are restored after each Feign call, covering the exception, timeout, and retry terminal states — not only the success path.

### Step 5: Verify with real round-trips

Run real Feign round-trips between two services covering context, tenant, error, and retry behavior, then report the interceptor inventory, evidence state, and remaining risk.

## Gotchas

- Feign client calls run on a different thread than the originating request — context must be captured before the call and cleared after, and every retry attempt re-enters that capture/clear cycle.
- Retries on non-idempotent endpoints duplicate side effects: a retry policy without per-endpoint idempotency analysis turns a transient timeout into a double charge or double order.
- Error handling done per-caller instead of through the error decoder factory forks the error contract — the same remote failure surfaces as different exceptions in different services.
- A Feign interface that compiles proves nothing: client registration, interceptor ordering, and a real round-trip are the evidence.
- Header allowlists that "just forward everything" leak Authorization headers and cookies to every downstream service on the call graph.
- Timeouts and retries interact: default read timeouts plus naive retries convert one slow downstream into a retry storm that finishes the outage.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；请求头示例仅使用脱敏的虚构值。

## Quick Start

- "Use `$ddd4j-cloud-feign` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-feign` to review existing usage against the current source."
- "Use `$ddd4j-cloud-feign` to return an implementation choice, evidence state, and remaining risk."

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
