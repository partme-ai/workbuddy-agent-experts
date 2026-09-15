---
name: ddd4j-boot-observability
description: Use when configuring or reviewing ddd4j-boot Actuator, health, readiness, metrics, tracing, logging, monitoring, or OpenTelemetry integration. 中文触发词：可观测性、Actuator、健康检查、指标、追踪、日志、监控、OpenTelemetry。
license: Apache-2.0
---

# ddd4j-boot Observability

## Overview

Covers Actuator, liveness/readiness, metrics, trace, logging, monitor, and OpenTelemetry uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Configuring Actuator exposure and separating liveness from readiness probes, with readiness aggregating real dependency checks.
- Wiring metrics (and the ddd4j metrics bridge) so domain and framework counters actually increment.
- Setting up tracing with OpenTelemetry and verifying the collector/exporter truly receives spans — not just that the SDK initializes.
- Deciding log formats and correlation (trace IDs in logs) across a Boot line's logging setup.
- Reviewing exporter lifecycle: exporters must have owners with idempotent close so shutdown does not drop or corrupt telemetry.
- Diagnosing "monitoring is configured but empty": beans present, endpoints responding, yet the backend shows no data.

## When NOT to Use

Do not use this skill when:

- **Metric names or the metrics SPI contract itself need designing** — use `ddd4j-metrics` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-metrics`.
- **The readiness endpoint's HTTP contract or the web-layer error contract is the question** — use `ddd4j-boot-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-web`.
- **Generic auto-configuration mechanics are the question, not telemetry** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The runtime is Quarkus, Javalin, or Spring Cloud** — use the matching `ddd4j-quarkus-*`, `ddd4j-javalin-*`, or `ddd4j-cloud-observability` skill instead; the Actuator assembly does not transfer.
- **The project is plain Spring Boot without ddd4j** — generic Actuator / Micrometer / OpenTelemetry skills apply.
- **Operational incident response on the live monitoring backend** — do not auto-expand into production operations; this skill configures and verifies, it does not operate.

## Trigger Keywords

**English**: observability, Actuator, health probes, metrics, tracing, logging, monitoring, OpenTelemetry

**中文**: 可观测性, Actuator, 健康检查, 指标, 追踪, 日志, 监控, OpenTelemetry
## Core Scope

Actuator, liveness/readiness, metrics, trace, logging, monitor, OpenTelemetry.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among observability implementations and Spring Boot assembly.
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

Run `ddd4j-boot-version-selection` to fix the line, then locate the Actuator, monitor, metrics, and OpenTelemetry AutoConfiguration and Properties on that line.

### Step 2: Design the observability set

Separate liveness from readiness — liveness must not fail because a dependency is down. Make readiness aggregate the real dependency checks, and plan the metrics, trace, and logging exporters against the actual observability backend.

### Step 3: Verify the wiring

Check conditional wiring, default beans, and user bean override points. Confirm the off switch truly skips assembly, and that exporters have explicit owners with rollback on failure and idempotent close.

### Step 4: Test the delivery

Execute context tests plus behavior tests: probe responses under dependency failure, metric increments on real operations, and export delivery verified at the collector/backend — not just at the SDK boundary.

### Step 5: Report with separated evidence

Report the chosen exporters and endpoints with configuration keys, the AutoConfiguration entry and override points, test results, and evidence state — configuration presence, bean creation, behavior, CI, and publish reported separately — plus risks and missing inputs.

## Gotchas

- An OTel SDK that initializes without errors proves nothing about delivery — spans can vanish at the exporter/collector boundary while the app logs nothing; verify at the backend.
- Liveness and readiness are different contracts: folding dependency checks into liveness makes a database hiccup restart every pod.
- Metrics endpoints responding 200 does not mean the counters are correct — increments must be tested against real operations, not endpoint availability.
- A user-declared metrics registry or exporter bean silently replaces the assembled default, and the boot module keeps exporting to a registry nobody reads.
- Actuator endpoint exposure and availability are separate settings on Boot 2/3/4 lines; an exposed-but-disabled endpoint (or vice versa) answers 404 while the config "looks enabled".
- Batched or buffered exporters that never close drop the last telemetry window at shutdown — the loss appears exactly during deploys and crashes.
- Printing Actuator or OTel configuration can leak endpoints, keys, and sampled payloads — sensitive values must be redacted.

## Output and Exceptions

When information is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output credentials, tokens, production connection strings, or sensitive business data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；指标与日志示例均已脱敏。

## Quick Start

- "Use `$ddd4j-boot-observability` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-observability` to review existing usage against the current source."
- "Use `$ddd4j-boot-observability` to return an implementation choice, evidence state, and remaining risk."

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
