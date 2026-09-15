---
name: ddd4j-javalin-release
description: Use when validating, checking CI, publishing, or remotely consuming ddd4j-javalin 6.7.x, 7.1.x, and 7.2.x with their JDK, Maven, POM, and private repository contracts. 中文触发词：发布验证、CI 门禁、私服发布、空缓存消费、Maven 4 断点续传、安全扫描、维护线验证。
license: Apache-2.0
---

# ddd4j-javalin Release

## Overview

Covers the three-line clean build, Git SHA, CI, Security, private repository deploy, clean-cache consumption, and Maven 4 resume uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Validating a maintenance line for release — clean build on its own JDK/Maven/POM contract for feature/6.7.x, feature/7.1.x, or feature/7.2.x, plus the Security stage with waivers recorded as `SKIPPED` risks.
- Gating on CI: resolving the required Actions jobs for the exact final SHA and waiting for terminal job conclusions.
- Executing an explicitly authorized private Maven deployment: serial per-line deploys, complete module inventory, and remote metadata capture.
- Proving remote availability with isolated empty-cache consumption (`-U`), never a warm local repository.
- Recovering a Maven 4 partial publication via `target/resume.properties` and revalidating the full inventory afterward.

## When NOT to Use

Do not use this skill when:

- **Plan approval, cross-capability release gating, or production-acceptance sign-off is the question** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **The maintenance line itself must be chosen or verified** — use `ddd4j-javalin-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-version-selection`.
- **Test suites must be designed or executed before the release gate** — use `ddd4j-javalin-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-testing`.
- **Spring Boot, Quarkus, or Spring Cloud releases are the question** — use `ddd4j-boot-release`, `ddd4j-quarkus-release`, or `ddd4j-cloud-release` instead, for example Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-release`.
- **CI is blocked by organization billing and credentials are suspected** — do not use this skill to rotate `MAVEN_SETTINGS_XML` or change billing; report CI as `BLOCKED (infrastructure)` and route the authorization boundary through `ddd4j-javalin-production-hardening`.
- **The project publishes a generic Maven build without ddd4j** — do not use this skill; use `java-skills` instead, since the three-line maintenance contract does not exist there.

## Trigger Keywords

**English**: release validation, CI gating, private Maven publish, empty-cache consumption, Maven 4 resume, security stage, maintenance line

**中文**: 发布验证, CI 门禁, 私服发布, 空缓存消费, Maven 4 断点续传, 安全扫描, 维护线验证

## Core Scope

Three-line clean build, Git SHA, CI, Security, private repository deploy, clean-cache consumption, Maven 4 resume.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for release work and Javalin adaptation.
- Lifecycle, configuration, and behavior boundaries.
- Differences across the three maintenance lines.

### ⚠️ Needs Input

- Target branch, POM, and Javalin version.
- Business behavior, dependencies, and deployment mode.
- Current source/test/CI evidence.

### ❌ Out of Scope

- Copying Javalin 6 code directly to 7.
- Substituting smoke tests for real behavior.
- Unauthorized releases or production changes.

## Workflow

### Step 1: Confirm the lines and SHAs

Fix the target lines (feature/6.7.x, feature/7.1.x, feature/7.2.x) with `ddd4j-javalin-version-selection`, record each checkout's exact Git SHA, and confirm the worktrees are clean before any build.

### Step 2: Build per line

Run a clean build for each line on its own toolchain — 6.7.x/7.1.x on JDK 17/Maven 3, 7.2.x on JDK 21/Maven 4. Run the Security stage and record any waived gate as a `SKIPPED` risk, never as a pass.

### Step 3: Gate on CI

Confirm the required Actions jobs reached terminal success for the exact final SHA of each line. A created or in-progress run is not a pass, and billing-blocked CI is `BLOCKED` — never translated into green.

### Step 4: Publish and prove consumption

Deploy serially to the private Maven repository only after explicit authorization, capturing branch, SHA, toolchain, and complete module inventory per line. Prove remote availability with isolated empty-cache resolution (`-U`) and verify the Maven 4 resume state via `target/resume.properties` when applicable.

### Step 5: Report per line

Produce a single report: per-line build, CI, Security, publish, and consumption results; evidence grading per tier with exact SHAs; the `BLOCKED`/`SKIPPED` inventory and remaining risks; redacted errors only, never credentials.

## Gotchas

- A CI run being created is not CI passing — resolve the run for the exact final SHA and wait for terminal required-job conclusions.
- Actions blocked by organization billing is `BLOCKED (infrastructure)`, not a code failure; rotating `MAVEN_SETTINGS_XML` or touching billing for it is actively harmful.
- Maven 4 and first-time SNAPSHOT metadata can fail with an RFC9457 JSON 404 after some uploads already succeeded — that is partial publication; inspect `target/resume.properties` and never report success from upload log lines.
- A warm `~/.m2`, local `install`, or producer-reactor success is not remote-consumer proof; only isolated empty-cache resolution with `-U` proves the private remote serves the artifacts.
- A security gate waived is `SKIPPED (risk retained)` — never `PASS` — and the retained risk must be reported per line.
- Publish the maintenance lines serially and stop at the first partial failure; the family release is not complete while one line is partial.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；发布输出仅报告凭据来源并脱敏，示例仅使用虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-release` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-release` to review existing usage against the current source."
- "Use `$ddd4j-javalin-release` to return an implementation choice, evidence state, and remaining risk."

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
