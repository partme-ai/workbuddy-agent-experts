---
name: ddd4j-boot-testing
description: Use when testing ddd4j-boot auto-configurations and functional integrations with ApplicationContextRunner, slice tests, maintenance matrices, HTTP contracts, databases, Redis, or Testcontainers. 中文触发词：测试、自动配置测试、维护矩阵、HTTP 契约、数据库、Redis、Broker、Testcontainers。
license: Apache-2.0
---

# ddd4j-boot Testing

## Overview

Covers ApplicationContextRunner, slice, matrix, HTTP, database, Redis, Broker, and Testcontainers uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Testing a ddd4j-boot auto-configuration's conditional wiring and user-override paths with `ApplicationContextRunner` or slice tests.
- Building the test matrix across the 13 maintenance lines (Boot 2.3–4.1) so a fix on one line is verified on the others.
- Designing HTTP contract, database, Redis, and broker round-trip tests against real backends with Testcontainers.
- Deciding what evidence a verification claim needs: context, bean creation, real behavior, CI, and publishing kept separate.
- Recording an honest run inventory — which suites passed, which are BLOCKED because Docker is unavailable, which were SKIPPED.
- Reviewing an existing test suite for gaps: untested override paths, missing disabled-state coverage, or skipped container suites counted as passes.

## When NOT to Use

Do not use this skill when:

- **The integration's behavior itself must be designed or fixed (not just tested)** — use the matching feature skill (`ddd4j-boot-data`, `ddd4j-boot-cache`, `ddd4j-boot-mq`, `ddd4j-boot-web`) instead.
- **Domain model tests without Boot wiring (aggregate, event replay, command) are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **The runtime is Javalin, Quarkus, or Spring Cloud** — use the matching `ddd4j-javalin-testing`, `ddd4j-quarkus-testing`, or `ddd4j-cloud-testing` skill instead; the Boot test fixtures do not transfer.
- **The release gate decision (what evidence blocks a release) is the question** — use `ddd4j-boot-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-release`.
- **The project is plain Spring Boot without ddd4j** — generic Spring Boot Test / Testcontainers skills apply; the ddd4j consistency matrix does not exist there.
- **CI infrastructure or Docker availability itself needs building** — this skill should not provision runners; it records Docker-unavailable suites as BLOCKED.

## Trigger Keywords

**English**: auto-configuration tests, ApplicationContextRunner, slice tests, maintenance matrix, HTTP contract, database round-trip, Testcontainers, BLOCKED suite

**中文**: 测试, 自动配置测试, 维护矩阵, 切片测试, HTTP 契约, 数据库往返, Testcontainers, 跳过即阻塞

## Core Scope

ApplicationContextRunner, slice, matrix, HTTP, database, Redis, Broker, Testcontainers.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among testing implementations and Spring Boot assembly.
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

1. Select the version line.
2. Locate the feature's aggregator and concrete implementations.
3. Compare implementations, defaults, overrides, and degradation.
4. Execute target context and behavior tests.
5. Output version, configuration, lifecycle, evidence, and risks.

## Workflow

### Step 1: Confirm the source of truth

Run `ddd4j-boot-version-selection` to fix the line, then locate the target module's `src/test`, the consistency scripts, and the Testcontainers fixtures available on that line.

### Step 2: Design the test matrix

Plan `ApplicationContextRunner` and slice tests for conditional wiring and user-override paths. Plan HTTP contract, database, Redis, and broker round-trips against real backends — in-memory doubles only prove wiring.

### Step 3: Execute the suites

Run the context and behavior suites for the target modules, and the container-based suites wherever Docker is available. Record the line, JDK, and Maven used alongside each result.

### Step 4: Record the evidence honestly

Mark Docker-unavailable or skipped suites BLOCKED/SKIPPED — never PASS. Keep configuration presence, bean creation, behavior, CI, and publish evidence as separate layers in the inventory.

### Step 5: Report the matrix and the gaps

Report the suites executed with line/JDK/Maven, the pass/fail plus BLOCKED/SKIPPED inventory, coverage against the feature matrix, the gaps found, and each risk with a proposed fix and missing inputs.

## Gotchas

- A context that starts proves bean creation, not behavior — an `ApplicationContextRunner` assertion and a real round-trip are different evidence layers.
- A Docker-unavailable suite that silently skips round-trips still reports green; a green run with hidden skips proves nothing and must be surfaced as BLOCKED/SKIPPED.
- Slice tests and full-context tests can disagree: a bean that assembles in the slice may be vetoed in the full context by a condition the slice does not evaluate.
- The 13 maintenance lines do not share test fixtures — a fixture passing on Boot 2.x can fail to compile on Boot 3.x+ (javax/jakarta); the matrix exists because per-line verification is not optional.
- A user-override path that was never tested is an unverified claim: `@ConditionalOnMissingBean` behavior must be exercised with a user bean present, not inferred.
- Testcontainers tests against one broker version do not transfer to the version the production line pins; pin the container image to the version the line's BOM manages.
- Printing test configuration dumps can leak credentials from the environment — sensitive values must be redacted.

## Output and Exceptions

When information is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output credentials, tokens, production connection strings, or sensitive business data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-boot-testing` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-testing` to review existing usage against the current source."
- "Use `$ddd4j-boot-testing` to return an implementation choice, evidence state, and remaining risk."

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
