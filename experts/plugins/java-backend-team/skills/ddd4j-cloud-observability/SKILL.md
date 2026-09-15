---
name: ddd4j-cloud-observability
description: Use when configuring or reviewing ddd4j-cloud Nacos, Sentinel, monitoring, tracing, metrics, logging, service health, or readiness behavior. 中文触发词：注册中心、配置中心、熔断限流、链路追踪、监控指标、日志、健康检查。
license: Apache-2.0
---

# ddd4j-cloud Observability

## Overview

Covers Nacos, Sentinel, monitor, trace, metrics, logging, health, and readiness uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Configuring Nacos registration/configuration and Sentinel rules with real connectivity in a ddd4j-cloud service.
- Separating liveness from readiness and wiring readiness to aggregate real dependencies.
- Planning and verifying trace propagation across sync, async, Reactor, and Feign paths.
- Reviewing metrics and logging for low-cardinality, redacted labels.
- Reviewing the monitor/nacos/sentinel extensions and their configuration keys.
- Diagnosing probes that stay green while a dependency is down, or rules that never fire.

## When NOT to Use

Do not use this skill when:

- **Request context propagation mechanics are the question** — use `ddd4j-cloud-context` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-context`.
- **Readiness wiring at the web/probe-contract level is the question** — use `ddd4j-cloud-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-web` (this skill owns Nacos/Sentinel connectivity and their extension configuration).
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-observability` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-observability`.
- **The runtime is Javalin** — use `ddd4j-javalin-production-hardening` or `ddd4j-javalin-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **Cluster-wide Prometheus/Grafana or alerting infrastructure without ddd4j** — do not use this skill; that is generic infrastructure tooling (no install command).
- **Building, publishing, or consuming artifacts is the goal** — use `ddd4j-cloud-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-release`.

## Trigger Keywords

**English**: service registry, circuit breaking, rate limiting, trace propagation, metrics, logging, health and readiness

**中文**: 注册中心, 配置中心, 熔断限流, 链路追踪, 监控指标, 日志, 就绪检查

## Core Scope

Nacos, Sentinel, monitor, trace, metrics, logging, health, readiness.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for observability and Spring Cloud integration.
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

Run `ddd4j-cloud-version-selection` to fix the combination, then locate the monitor/nacos/sentinel extensions and their tests on the confirmed branch and SHA.

### Step 2: Design the observability set

Separate liveness from readiness — readiness aggregates real dependencies including Nacos and Sentinel. Plan trace propagation, metrics, and logging against the actual backend.

### Step 3: Wire external services

Configure Nacos registration/configuration and Sentinel rules with real connectivity. Mark any untestable external behavior NOT VERIFIED rather than assuming success.

### Step 4: Test the observability surface

Verify probes respond per dependency state. Verify trace context propagation across sync, async, Reactor, and Feign paths, and that metrics and logs carry low-cardinality, redacted labels.

### Step 5: Report the observability state

Output the extension inventory with configuration keys, probe behavior per dependency state with evidence per tier, tests executed and remaining gaps, and risks with proposed fixes.

## Gotchas

- Nacos/Sentinel presence in the classpath does not mean the server is reachable — startup can succeed while the dependency is down, and registration or rule delivery is silently broken.
- Liveness must not depend on external services: wiring a Nacos check into liveness turns every registry blip into a pod restart cascade.
- Trace context behaves like any thread-bound context — it does not cross `@Async`, Reactor, or Feign boundaries without explicit propagation, so traces fragment exactly on the async paths.
- High-cardinality labels (user ids, tenant ids, request ids) on metrics explode the monitoring backend; keep cardinality low and move identity into traces or logs.
- Sentinel rules configured in the app do nothing if the rule-push channel to the dashboard/cluster is not connected — the rules exist but never activate.
- Nacos configuration values can contain secrets: never print or export them; redact before any output.
- A green startup log is not evidence — registration, rule delivery, and probe behavior need real verification or an explicit NOT VERIFIED mark.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；日志与配置示例均经脱敏，不含真实凭据。

## Quick Start

- "Use `$ddd4j-cloud-observability` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-observability` to review existing usage against the current source."
- "Use `$ddd4j-cloud-observability` to return an implementation choice, evidence state, and remaining risk."

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
