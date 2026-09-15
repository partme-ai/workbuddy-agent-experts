---
name: ddd4j-cloud-version-selection
description: Use when choosing a ddd4j-cloud line based on Spring Cloud, Spring Boot, ddd4j, JDK, Maven, POM model, and main versus compatibility pairing constraints. 中文触发词：版本选择、兼容矩阵、维护组合、维护线、JDK 对应、Maven 版本、POM 模型、升级路径。
license: Apache-2.0
---

# ddd4j-cloud Version Selection

## Overview

Covers the complete Hoxton.x, 2020.0.x, 2021.0.x, 2022.0.x, 2023.0.x, 2024.0.x, 2025.0.x, and 2025.1.x matrix uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Choosing the Spring Cloud line (Hoxton.x through 2025.1.x) and its matching Boot parent and ddd4j line for a new or existing service.
- Deciding whether a compatible alternative may substitute the primary Cloud→Boot→ddd4j combination.
- Planning an upgrade from one of the eight maintenance lines to another.
- Auditing a POM whose Cloud/Boot/ddd4j triple may not be a real, verified pairing.
- Determining whether old `cmpt` naming must be migrated to canonical `extensions` naming on the target line.
- Classifying a blocked build as BLOCKED(upstream), BLOCKED(infrastructure), or a Cloud-side defect.

## When NOT to Use

Do not use this skill when:

- **The project is plain Spring Boot ddd4j wiring with no Spring Cloud dependency** — use `ddd4j-boot-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-version-selection`.
- **The runtime is Javalin or Quarkus** — use `ddd4j-javalin-version-selection` or `ddd4j-quarkus-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-version-selection` (or `--skill ddd4j-quarkus-version-selection`).
- **BOM import order or version ownership inside ddd4j-cloud is the question** — use `ddd4j-cloud-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-bom`.
- **Module layout and upstream boundaries are the question** — use `ddd4j-cloud-architecture` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-architecture`.
- **Generic Java / Spring Cloud version selection without ddd4j** — do not use this skill; apply generic `java-skills` / `spring-cloud` guidance instead (no install command; never retrofit ddd4j version constraints onto a non-ddd4j codebase).
- **Core domain or SPI contracts are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.

## Trigger Keywords

**English**: version selection, compatibility matrix, maintenance combination, maintenance line, JDK mapping, Maven version, POM model, upgrade path

**中文**: 版本选择, 兼容矩阵, 维护组合, 维护线, JDK 对应, Maven 版本, POM 模型

## Core Scope

The complete Hoxton.x, 2020.0.x, 2021.0.x, 2022.0.x, 2023.0.x, 2024.0.x, 2025.0.x, and 2025.1.x matrix.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for version selection and Spring Cloud integration.
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

### Step 1: Select the primary combination

Read the eight-line matrix (Hoxton.x through 2025.1.x) mapping Cloud→Boot→ddd4j and confirm the pairing from the branch's POMs and `verify_cloud_release_matrix.py`, never from the branch name. Keep compatible alternatives listed separately from the primary.

### Step 2: Locate extensions and dependencies

Confirm the line uses canonical `extensions` naming with no old `cmpt` references, then enumerate upstream Boot/ddd4j artifacts and the external services (binder, database, Nacos, Sentinel) the combination requires.

### Step 3: Compare implementations across lines

For the candidate versus the current line, compare the propagation, degradation, and lifecycle behavior of the modules you actually use — these differences are the migration risk.

### Step 4: Verify the evidence

Build and test the selected combination, check CI for the final SHA, and prove consumption from the private repository with a clean cache before declaring the choice valid.

### Step 5: Report the choice

Output version, implementation, external dependencies, and risks, with BLOCKED(upstream) and BLOCKED(infrastructure) items separated and missing inputs listed as "missing: specific item; how to provide: path or configuration".

## Gotchas

- The branch name does not determine Boot/ddd4j versions — the pairing lives in the line's POMs and the matrix; guessing from the name is the top anti-pattern.
- A compatible alternative is not the primary combination — treating alternative parity as validated hides version-specific behavior differences.
- A class existing in source does not prove the capability works; registration and behavior evidence are also required.
- Configuration presence does not mean the server is reachable — startup can succeed while Nacos, Sentinel, or the broker is down.
- Binder names do not carry across brokers — physical destinations differ, so a line switch that changes binder defaults can silently retarget messages.
- Misclassified blockers send fixes to the wrong team: a missing Boot/ddd4j artifact is BLOCKED(upstream); a CI run that never started is BLOCKED(infrastructure).
- Old `cmpt` coordinates can still resolve in a consumer dependency graph after the hard cut — audit the transitive graph, not just the direct POM.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-cloud-version-selection` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-version-selection` to review existing usage against the current source."
- "Use `$ddd4j-cloud-version-selection` to return an implementation choice, evidence state, and remaining risk."

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
