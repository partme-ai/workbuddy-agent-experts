---
name: ddd4j-boot-release
description: Use when validating, committing, checking CI, publishing, or remotely consuming multiple ddd4j-boot maintenance lines with their required JDK, Maven, POM, and private repository contracts. 中文触发词：发布验证、13 条维护线、CI 门槛、私服部署、空缓存消费、Git SHA、远端可用性。
license: Apache-2.0
---

# ddd4j-boot Release

## Overview

Covers the 13-line clean build, Git SHA, CI, Security, private repository deploy, and clean-cache consumption uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Validating a release across the 13 maintenance lines: per-line clean build with its required JDK and Maven (2.3→4.1, JDK 8→21).
- Gating a release on CI jobs reaching terminal success for the final Git SHA — and reporting non-started CI as BLOCKED, never PASS.
- Running the Security stage and recording exemptions as SKIPPED risks rather than silently passing.
- Deploying artifacts to the private repository and confirming the deploy exited zero with complete remote metadata.
- Proving remote availability by consuming from an isolated clean Maven cache (`-U`) — the warm-cache false green is this skill's central enemy.
- Producing the per-line evidence grading (SOURCE/TEST/CI/PUBLISHED/CONSUMED) that downstream consumers rely on.

## When NOT to Use

Do not use this skill when:

- **The release has not been validated anywhere and no line was chosen** — use `ddd4j-boot-version-selection` first. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-version-selection`.
- **The test suites themselves must be designed or run** — use `ddd4j-boot-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-testing`.
- **The runtime is Javalin, Quarkus, or Spring Cloud** — use the matching `ddd4j-javalin-release`, `ddd4j-quarkus-release`, or `ddd4j-cloud-release` skill instead; the 13 Boot lines are not their lines.
- **Cross-product parent/BOM authority is the question** — use `ddd4j-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-bom`.
- **The project is plain Spring Boot without ddd4j** — generic Maven release / CI skills apply; the per-line evidence grading does not exist there.
- **An actual production rollout or hotfix operation is requested** — do not use this skill to operate production; it should not act without explicit authorization and stays within validation and publication.

## Trigger Keywords

**English**: release validation, 13 maintenance lines, CI gate, private repository deploy, clean-cache consumption, Git SHA, evidence grading, security exemptions

**中文**: 发布验证, 13 条维护线, CI 门槛, 私服部署, 空缓存消费, Git SHA, 证据分级, 安全豁免

## Core Scope

13-line clean build, Git SHA, CI, Security, private repository deploy, clean-cache consumption.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among release implementations and Spring Boot assembly.
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

Run `ddd4j-boot-version-selection` to fix the target lines, then record the Git SHA of each checkout and confirm the worktree is clean — a dirty tree invalidates every downstream evidence claim.

### Step 2: Build every line

Run a clean build per line with its required JDK and Maven (13 lines when validating all), then run the Security stage. Mark security exemptions as SKIPPED and carry them forward as risks — do not silently pass them.

### Step 3: Gate on CI

Confirm the required CI jobs reached terminal success for the final SHA. A non-started CI run is BLOCKED, never PASS; a green run for an earlier SHA proves nothing about the final code.

### Step 4: Publish and consume

Deploy to the private repository, confirm the deploy exited zero with complete remote metadata, then consume the artifacts from an isolated clean Maven cache (`-U`) to prove remote availability.

### Step 5: Report the per-line evidence

Report per-line build, CI, Security, publish, and consumption results with the SOURCE/TEST/CI/PUBLISHED/CONSUMED grading, the BLOCKED/SKIPPED inventory, remaining risks, and redacted errors only — never credentials or tokens.

## Gotchas

- A green build on the release machine proves nothing about remote availability — only consumption from an isolated clean cache (`-U`) distinguishes PUBLISHED from merely local.
- CI green for an earlier SHA does not gate the final code; commits after the run invalidate the claim, so the SHA must match exactly.
- A non-started CI job and a passing CI job produce different evidence, but dashboards often render both as "done" — non-started must be recorded BLOCKED explicitly.
- Security exemptions that pass silently reappear as audit findings; a SKIPPED security stage is a risk to carry, not a check to green.
- Deploy exiting zero does not guarantee complete remote metadata; consumers on other lines can fail resolution against an incomplete deploy.
- The 13 lines build on different toolchains (JDK 8→21, Maven 3 and 4) — a release pipeline that unifies the toolchain validates nothing for the lines it misbuilds.
- Error output from deploys can embed repository credentials — only redacted errors may be shown.

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

- "Use `$ddd4j-boot-release` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-release` to review existing usage against the current source."
- "Use `$ddd4j-boot-release` to return an implementation choice, evidence state, and remaining risk."

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
