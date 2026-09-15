---
name: ddd4j-cloud-context
description: Use when implementing or reviewing ddd4j-cloud request header, ThreadContext, asynchronous task, Reactor context, Feign propagation, restoration, or cleanup behavior. 中文触发词：上下文传播、线程上下文、异步传播、Reactor 上下文、Feign 传播、上下文清理。
license: Apache-2.0
---

# ddd4j-cloud Context

## Overview

Covers request headers, ThreadContext, async threads, Reactor, Feign, restoration, and cleanup uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Propagating request headers into `ThreadContext` at service entry in a ddd4j-cloud service.
- Making context survive `@Async` executors, Reactor operators, or Feign calls.
- Verifying restoration on sync, async, Reactor, and Feign terminal states.
- Auditing cleanup on success, exception, and thread-pool reuse paths.
- Reviewing the core/data/web/feign context filters and their tests on a line.
- Diagnosing cross-request data bleed on pooled threads or missing headers after a Feign hop.

## When NOT to Use

Do not use this skill when:

- **Tenant isolation semantics are the question** (data scope, SQL filtering, ignore rules) — use `ddd4j-cloud-tenant` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-tenant`.
- **Feign plumbing is the question** (interceptor registration, error decoder factory, retry policy) — use `ddd4j-cloud-feign` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-feign`.
- **The ThreadLocal/Subject SPI contracts themselves are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-web`.
- **The runtime is Javalin or Quarkus** — use the matching `ddd4j-javalin-*` / `ddd4j-quarkus-*` skill instead (for example `ddd4j-javalin-web`, `ddd4j-quarkus-runtime`).
- **Generic Spring Cloud context propagation without ddd4j** — do not use this skill; apply generic `spring-cloud` guidance instead (no install command).

## Trigger Keywords

**English**: context propagation, thread context, async propagation, Reactor context, Feign propagation, context restoration, context cleanup

**中文**: 上下文传播, 线程上下文, 异步传播, Reactor 上下文, Feign 传播, 上下文清理

## Core Scope

Request headers, ThreadContext, async threads, Reactor, Feign, restoration, and cleanup.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for context and Spring Cloud integration.
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

Run `ddd4j-cloud-version-selection` to fix the combination, then locate the core/data/web/feign context filters and their tests on the confirmed branch and SHA.

### Step 2: Map the propagation surface

Enumerate the entry points — request headers, `ThreadContext`, async executors, Reactor, and Feign calls — and identify which extension owns each hop.

### Step 3: Verify restoration and cleanup

Confirm restoration on sync, async, Reactor, and Feign terminal states, and cleanup on success, exception, and thread-pool reuse — no residue may survive across requests.

### Step 4: Test the hops

Run propagation tests across every hop, deliberately including exception and pool-reuse paths, and verify cross-service headers survive a real Feign round-trip.

### Step 5: Report the propagation map

Output the propagation map (hop → mechanism → owner) with file paths, restoration/cleanup coverage per terminal state, tests executed with evidence state per tier, and violations with proposed fixes.

## Gotchas

- A `ThreadLocal`-backed context does not cross an `@Async` boundary or a Reactor operator — each hop needs explicit propagation, and Reactor can hop threads between operators, so restoring only at subscription start is insufficient.
- Feign client calls run on a different thread than the originating request — context must be captured before the call and cleared after, and each retry attempt re-enters that cycle.
- Cleanup wired only on the success path leaks on exceptions: a pooled thread returns with the previous request's Subject or tenant bound and serves it to the next request.
- A context filter class existing in source proves nothing — it must be registered in the filter chain for the line, in the right order.
- Two context mechanisms on the classpath (for example a surviving old `cmpt` filter) can each restore half the state and mask each other's failures.
- Propagated headers need an allowlist — blindly forwarding all inbound headers leaks credentials to downstream services.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；上下文与用户标识示例均为虚构数据。

## Quick Start

- "Use `$ddd4j-cloud-context` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-context` to review existing usage against the current source."
- "Use `$ddd4j-cloud-context` to return an implementation choice, evidence state, and remaining risk."

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
