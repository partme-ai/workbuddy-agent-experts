---
name: ddd4j-boot-web
description: Use when building ddd4j Spring MVC or WebFlux applications with unified errors, request context, authentication, validation, idempotency, CORS, limits, and readiness. 中文触发词：Web 集成、MVC/WebFlux、Context 绑定、统一错误、校验、幂等、CORS、就绪检查。
license: Apache-2.0
---

# ddd4j-boot Web

## Overview

Covers Spring MVC, WebFlux, Context, errors, authentication, Validation, idempotency, CORS, and Readiness uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Choosing Spring MVC versus WebFlux for a ddd4j-boot service and assembling it from the `ddd4j-web-webmvc` / `ddd4j-webflux` modules.
- Unifying the error contract so domain and framework failures return one consistent response shape.
- Binding the ddd4j request `Context` (Subject, tenant) into the web request lifecycle — and releasing it on every exit path.
- Configuring validation, idempotency keys, CORS allowlists, and rate/concurrency limits through the boot web auto-configuration.
- Wiring readiness so it aggregates real dependency health instead of a hardcoded READY.
- Diagnosing web-layer issues on a specific Boot line (2.3–4.1): errors leaking stack traces, context not bound on async paths, or readiness reporting healthy while a dependency is down.

## When NOT to Use

Do not use this skill when:

- **The error response contract or context contract itself needs designing** — use `ddd4j-core` (context/subject contracts) or `ddd4j-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-web`.
- **The authentication framework choice and SubjectProvider assembly are the question** — use `ddd4j-boot-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-auth`.
- **Generic auto-configuration mechanics are the question, not the web layer** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The runtime is Javalin, Quarkus, or Spring Cloud** — use the matching `ddd4j-javalin-web`, `ddd4j-quarkus-web`, or `ddd4j-cloud-web` skill instead; the MVC/WebFlux assembly does not transfer.
- **The project is plain Spring Boot without ddd4j** — generic Spring MVC / WebFlux skills apply; the ddd4j context binding and error contract do not exist there.
- **Metrics, traces, and health endpoints need building** — use `ddd4j-boot-observability` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-observability`.

## Trigger Keywords

**English**: web integration, MVC/WebFlux, context binding, unified errors, validation, idempotency, CORS, readiness

**中文**: Web 集成, MVC/WebFlux, Context 绑定, 统一错误, 校验, 幂等, CORS, 就绪检查
## Core Scope

Spring MVC, WebFlux, Context, errors, authentication, Validation, idempotency, CORS, Readiness.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among web implementations and Spring Boot assembly.
- Configuration, overrides, lifecycle, and verification.
- Maintenance-line compatibility judgments.

### ⚠️ Needs Input

- Target Boot line, POM, and configuration.
- Business behavior, dependencies, and deployment mode.
- Current test/CI/runtime evidence.

### ❌ Out of Scope

- Modifying ddd4j core public semantics.
- Substituting dependency or bean presence for real behavior.
- Unauthorized releases or production operations.

## Workflow

### Step 1: Confirm the source of truth

Run `ddd4j-boot-version-selection` to fix the line, then locate the web AutoConfiguration, its Properties, and the `ddd4j-web-webmvc` / `ddd4j-webflux` modules on that line.

### Step 2: Select the web stack

Choose Spring MVC or WebFlux against the workload's blocking profile, and confirm the context binding, error handling, and authentication wiring for that stack — the two stacks bind and release the request `Context` differently.

### Step 3: Verify the wiring

Check conditional wiring, default beans, and user bean override points. Confirm validation, idempotency, the CORS allowlist, limits, and readiness are configured from the line's Properties — each with a real off switch that skips assembly.

### Step 4: Test the HTTP contract

Execute context tests plus HTTP contract tests covering normal, error, replay (idempotency), and async paths. Confirm readiness aggregates real dependency checks and never hardcodes READY, and that the request `Context` is released on success, error, and async completion.

### Step 5: Report with separated evidence

Report the chosen web stack with configuration keys, the AutoConfiguration entry and override points, test results, and evidence state — configuration presence, bean creation, behavior, CI, and publish reported separately — plus risks and missing inputs.

## Gotchas

- MVC and WebFlux bind and release the request `Context` at different points; wiring tuned for MVC leaks or misses the context on WebFlux async paths even when "the filter is registered".
- A readiness endpoint that returns hardcoded READY passes every smoke test and lies precisely when it is needed — readiness must aggregate real dependency checks.
- A unified error handler registered as one bean does not cover validation failures raised before the handler chain — the error contract must be tested for the validation path specifically.
- MVC and WebFlux cannot both be fully assembled; the second starter on the classpath typically wins silently and the "wrong" stack serves the requests.
- Idempotency replay behavior differs per line's Properties semantics; a replay test (same key, same body) must be run, not inferred from the config key existing.
- A CORS allowlist read from environment-specific config that falls back to `*` in an unconfigured environment passes local tests and is wide open in staging.
- Printing web configuration for troubleshooting can leak hosts, keys, and tokens — sensitive values must be redacted.

## Output and Exceptions

When information is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output credentials, tokens, production connection strings, or sensitive business data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；请求与响应示例均为脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-boot-web` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-web` to review existing usage against the current source."
- "Use `$ddd4j-boot-web` to return an implementation choice, evidence state, and remaining risk."

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
