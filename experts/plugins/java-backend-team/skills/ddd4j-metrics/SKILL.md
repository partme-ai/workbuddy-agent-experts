---
name: ddd4j-metrics
description: Use when instrumenting or reviewing ddd4j projection, runtime, Web, MQ, cache, or domain-operation metrics, especially OpenTelemetry counters, timers, failures, labels, and observability evidence. 中文触发词：指标设计、OpenTelemetry、Projection 指标、标签基数、监控告警、可观测性、Noop 降级。
license: Apache-2.0
---

# ddd4j Metrics

## Overview

Metrics must describe observable behavior and keep cardinality low; the current first-party implementation centers on ProjectionMetrics and OpenTelemetryProjectionMetrics, with other capabilities extended per real adapter.

## When to Use

- Instrumenting projections via the `ProjectionMetrics` port and the `OpenTelemetryProjectionMetrics` adapter — success/failure, processed count, duration, position lag.
- Designing metric sets for Web, MQ, Cache, or Runtime capabilities (request count, ack/nack, hit/miss, startup/readiness).
- Reviewing label design and rejecting high-cardinality or PII-bearing labels (tenant, user id, message id).
- Deciding whether a `Noop` metrics implementation means observability is present (it does not — it is a degradation).
- Writing metric tests: names, label sets, increments, and exception paths.
- Distinguishing what metrics can claim from what logs, traces, readiness, and business acceptance must prove separately.

## When NOT to Use

Do not use this skill when:

- **The OpenTelemetry extension module's dependency, classpath guard, or wiring is the question** — use `ddd4j-extensions` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-extensions`; this skill owns metric design, not module integration.
- **Readiness/liveness or health aggregation is the question** — use `ddd4j-web` or `ddd4j-runtime` instead; metrics are not a readiness signal. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-web`.
- **Log and trace design is the question** — metrics, logs, and traces are separate evidence classes; generic observability skills apply for non-metric telemetry.
- **A request asks to invent metrics that no port or adapter actually provides** — do not use this skill to fabricate an inventory; record only what the source provides or explicitly plans.
- **Dashboard/backend operations (Grafana provisioning, collector ops) with no ddd4j instrumentation involved** — use the backend's own tooling and the generic `java-skills`.

## Trigger Keywords

**English**: metrics design, OpenTelemetry, projection metrics, label cardinality, success failure counters, noop degradation, observability evidence, metric testing

**中文**: 指标设计, OpenTelemetry, Projection 指标, 标签基数, 成功失败计数, Noop 降级, 可观测性, 监控告警

## Core Rules

1. Ports are defined in the core capability; OpenTelemetry lives in the metrics/extension adapter.
2. success/failure, duration, and processed count are kept separate.
3. tenant/user/message id are not high-cardinality labels.
4. A Noop implementation is a degradation, not observability success.
5. Metric tests verify names, labels, increments, and exception paths.
6. Metrics cannot substitute for logs, traces, readiness, or business acceptance.

## Capability Boundaries

### ✅ Strong At

- ProjectionMetrics/OpenTelemetry.
- Web/MQ/Cache/Runtime metric design.
- Label cardinality and privacy review.
- Metric testing and evidence grading.

### ⚠️ Needs Input

- Observability backend and naming convention.
- SLI/SLO and alerting targets.
- Current instrumentation in the target modules.

### ❌ Out of Scope

- Inventing metrics that do not exist.
- PII as labels.
- Claiming production observability because metrics exist.

## Deep Reference

- [Projection Metrics](references/projection.md)
- [Cross-Capability Metrics](references/cross-capability.md)
- [Testing and Alerting](references/testing-and-alerting.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Workflow

### Step 1: Confirm the source of truth

Identify the modules to instrument, the observability backend, the naming convention, and the SLO/alerting targets. Metrics designed without a consumer question end up as noise.

### Step 2: Locate the ports and the real implementation

Find `ProjectionMetrics` / `NoopProjectionMetrics` in core and `OpenTelemetryProjectionMetrics` in the adapter. Confirm the runtime actually binds the real implementation where observability is required — Noop bound means observability is absent.

### Step 3: Design the metric set

Keep success/failure, duration, and processed count as separate series. Choose stable low-cardinality labels; exclude tenant, user id, message id, and any PII by rule, not by case-by-case judgment.

### Step 4: Implement and test behavior

Verify metric names, label sets, increments, and — critically — exception paths: a failure must record failure and must not advance a pseudo-success state. Cover the no-backend degradation path explicitly.

### Step 5: Wire alerting and prove the chain

Derive alerts from SLOs and distinguish transient, sustained, and no-data states. Verify end to end that the exporter/collector receives real data — a registered meter nobody receives is not observability.

## Gotchas

- Tenant, user id, or message id used as labels — each new value creates a new time series; the backend degrades under cardinality explosion and the dashboards that "worked in staging" fall over in production.
- `NoopProjectionMetrics` bound at runtime while the checklist says "metrics: done" — the Noop implementation compiles, registers, and records nothing; it is a degradation, not observability.
- Tests that only assert the meter registered — never asserting an increment — so a broken recording path passes the suite while production counters stay at zero.
- Exception paths not recorded — only successes counted, which makes the failure rate read as exactly 0.0 and hides the incident in progress.
- Metrics treated as a health/readiness signal — a projection can export perfect metrics while being objectively not ready; readiness is judged separately by the runtime/web contract.
- `CacheStats` presented as business success — hit/miss ratios describe the cache, not the business operation that the cached data serves.
- Inventing metric names that no port or adapter defines — the inventory must come from what the source actually provides or explicitly plans, not from what a dashboard template wants.

## Privacy and Security

Labels must not contain tokens, user IDs, phone numbers, full URLs, SQL, or message bodies. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；指标标签与示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-metrics` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-metrics` to review existing usage against the current source."
- "Use `$ddd4j-metrics` to return an implementation choice, evidence state, and remaining risk."

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
