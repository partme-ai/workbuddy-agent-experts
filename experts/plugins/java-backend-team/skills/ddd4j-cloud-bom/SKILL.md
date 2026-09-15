---
name: ddd4j-cloud-bom
description: Use when managing ddd4j-cloud parent, dependencies, BOM imports, Spring Cloud and Alibaba versions, Boot parent alignment, effective POM, or consumer coordinates. 中文触发词：BOM 导入、版本所有权、effective POM、Boot parent、Cloud/Alibaba 版本、依赖管理。
license: Apache-2.0
---

# ddd4j-cloud BOM

## Overview

Covers the Cloud/Alibaba BOM, Boot parent, ddd4j BOM, version ownership, and effective POM uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Managing the `cloud-parent`, `cloud-dependencies`, and `cloud-bom` POMs and their consumer coordinates.
- Choosing or verifying Spring Cloud and Spring Cloud Alibaba versions plus the aligned Boot parent.
- Auditing the effective POM and the BOM import order for a line.
- Deciding version ownership — which versions consumers may or may not override.
- Cleaning up extensions that re-pin managed versions.
- Preparing consumer coordinates for downstream clean-cache verification.

## When NOT to Use

Do not use this skill when:

- **Which Cloud→Boot→ddd4j combination to target is the question** — use `ddd4j-cloud-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-version-selection`.
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-bom`.
- **Module layout and upstream boundaries are the question** — use `ddd4j-cloud-architecture` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-architecture`.
- **A single service wants its own dependency versions** — do not use this skill; apply generic Maven `dependencyManagement` practice (`java-skills`, no install command). Import order and ownership of the ddd4j-cloud BOMs themselves always belong here.
- **Publishing the line or proving remote consumption is the goal** — use `ddd4j-cloud-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-release`.
- **Core domain or SPI contracts are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.

## Trigger Keywords

**English**: BOM import order, version ownership, effective POM, Boot parent, dependency management, consumer coordinates

**中文**: BOM 导入, 版本所有权, effective POM, Boot parent, 依赖管理, 消费坐标

## Core Scope

Cloud/Alibaba BOM, Boot parent, ddd4j BOM, version ownership, effective POM.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for BOM management and Spring Cloud integration.
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

Run `ddd4j-cloud-version-selection` to fix the combination, then read the `cloud-parent`, `cloud-dependencies`, and `cloud-bom` POMs on the confirmed branch and SHA.

### Step 2: Verify version ownership

Confirm Spring Cloud and Spring Cloud Alibaba versions come from their own BOMs, that the Boot parent alignment matches the combination matrix, and that no extension re-pins a managed version.

### Step 3: Verify import order

Build the effective POM and confirm the BOM import order resolves as intended — the order of `spring-cloud-dependencies`, the Alibaba BOM, and the ddd4j BOM changes the effective versions. Record consumer coordinates for downstream verification.

### Step 4: Validate the build

Run the target module build and tests on the selected combination and check CI for the final SHA.

### Step 5: Report the audit

Output the combination and effective-POM findings, the version ownership map with import-order confirmation, consumer coordinates with evidence state per tier, and violations with proposed fixes.

## Gotchas

- The Cloud BOM import order changes the effective version — importing `spring-cloud-dependencies` before the Alibaba BOM and the ddd4j BOM produces a different resolution than the reverse.
- The declared POM and the effective POM are different documents — ownership violations only show up in the effective resolution, not in reading sources.
- An extension that re-pins a "harmless" library version silently splits the line: two services on the same line can resolve different dependency graphs.
- Old `cmpt` coordinates in a consumer POM resolve against stale artifacts even when the current line only publishes `extensions`.
- A missing remote Boot/ddd4j artifact is BLOCKED(upstream), not a local POM bug — do not fix it by uploading a hand-made artifact.
- Deploying a corrected BOM without isolated clean-cache consumption proof leaves the previous resolution cached at consumers; the fix looks applied but is not.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；仓库地址与构件坐标示例均为脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-cloud-bom` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-bom` to review existing usage against the current source."
- "Use `$ddd4j-cloud-bom` to return an implementation choice, evidence state, and remaining risk."

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
