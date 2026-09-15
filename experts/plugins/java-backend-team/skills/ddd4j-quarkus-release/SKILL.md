---
name: ddd4j-quarkus-release
description: Use when validating, checking CI, publishing, or remotely consuming ddd4j-quarkus 3.3.x and 4.0.x with Maven 3 or 4, security status, module inventory, and private repository contracts. 中文触发词：验证发布、CI 门禁、Security 扫描、空缓存消费、私有仓库、模块清单、Git SHA、发布授权。
license: Apache-2.0
---

# ddd4j-quarkus Release

## Overview

Covers the dual-line clean build, Git SHA, CI, Security, private repository, 61 modules, and clean-cache consumption uniformly, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Validating the dual-line clean build: 3.3.x with Maven 3 / JDK 17, 4.0.x with Maven 4 / JDK 21.
- Recording the checkout's Git SHA and gating on CI terminal success for exactly that SHA.
- Recording Security scan outcomes honestly — SKIPPED is a risk carried into the report, never PASS.
- Publishing to the private repository after explicit authorization, verifying the complete 61-module inventory per deploy.
- Proving remote availability with isolated clean-cache consumption (`-U`) instead of a warm local cache.
- Reviewing a release report for evidence grading, skip inventory, and redacted credentials.

## When NOT to Use

Do not use this skill when:

- **The Spring Boot lines' validation and publishing are the question** — use `ddd4j-boot-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-release`.
- **Javalin line releases** — use `ddd4j-javalin-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-release`.
- **Spring Cloud line releases** — use `ddd4j-cloud-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-release`.
- **The test strategy before the gate is the question** — use `ddd4j-quarkus-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-testing`.
- **The maintenance line itself is not yet chosen** — use `ddd4j-quarkus-version-selection` first. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-version-selection`.
- **The project is a plain Quarkus codebase without ddd4j** — generic Maven/CI guidance applies; do not use the ddd4j release gates on a non-ddd4j stack. This skill also should not publish anything without explicit user authorization.

## Trigger Keywords

**English**: release validation, CI gate, security scan, clean-cache consumption, private repository, module inventory, Git SHA, publish authorization

**中文**: 验证发布, CI 门禁, Security 扫描, 空缓存消费, 私有仓库, 模块清单, Git SHA, 发布授权

## Core Scope

Dual-line clean build, Git SHA, CI, Security, private repository, 61 modules, clean-cache consumption.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for release work and Quarkus adaptation.
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

Fix the lines (3.3.x / 4.0.x) via `ddd4j-quarkus-version-selection`, record each checkout's Git SHA, and confirm clean worktrees — a dirty tree invalidates the build's claim to the SHA.

### Step 2: Build

Run a clean build per line with the matching toolchain (Maven 3 for 3.3.x, Maven 4 with JDK 21 for 4.0.x) and verify the complete 61-module inventory per deploy; zero exit without the full inventory is not a successful build.

### Step 3: Gate on CI and Security

Confirm the required CI jobs reached terminal success for the final SHA, and record Security skips as SKIPPED risks — never PASS and never silently dropped.

### Step 4: Publish and consume

Deploy to the private repository only after explicit authorization, requiring zero exit and the complete module inventory, then prove remote availability with isolated clean-cache consumption (`-U`).

### Step 5: Report

Produce a single report: per-line build, CI, Security, publish, and consumption results; evidence grading per tier with exact SHAs; the BLOCKED/SKIPPED inventory and remaining risks; redacted errors only — never credentials.

## Gotchas

- A green local build does not prove remote availability — a warm local cache hides the fact that the artifact was never published; consume with an isolated clean cache (`-U`) before declaring CONSUMED.
- CI success for an older SHA does not gate the final commit — the required jobs must have reached terminal success for the exact final SHA, not "the branch is green".
- Security SKIPPED is not PASS: a skipped scan is a risk that must be carried into the release report, not a checkbox.
- Maven 3 cannot build the 4.0.x line; Maven 4 / JDK 21 is part of the line contract, so "it built on my machine" claims must be checked against the toolchain too.
- Deploy exit code zero without the full 61-module inventory is a partial deploy — count the modules before declaring the publish successful.
- Publishing requires explicit user authorization; the release flow should never push artifacts on its own initiative, and every quoted error must be redacted of Maven settings, repository credentials, and tokens.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；发布报告与错误引用均先做脱敏处理。

## Quick Start

- "Use `$ddd4j-quarkus-release` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-release` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-release` to return an implementation choice, evidence state, and remaining risk."

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
