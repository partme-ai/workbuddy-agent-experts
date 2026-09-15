---
name: ddd4j-boot-version-selection
description: Use when choosing a compatible ddd4j-boot maintenance line for a Spring Boot project, upgrade, or legacy system based on Spring Boot, ddd4j, JDK, Maven, and POM model constraints. 中文触发词：版本选择、维护线、兼容矩阵、JDK 对应、Maven 版本、POM 模型、升级路径。
license: Apache-2.0
---

# ddd4j-boot Version Selection

## Overview

Spring Boot version and JDK are the entry points; the output is the complete Boot→ddd4j→JDK→Maven/POM tuple.

## When to Use

- Choosing the ddd4j-boot maintenance line for a new project, given the Spring Boot version and JDK the organization supports.
- Planning an upgrade that crosses ddd4j main lines (for example Boot 2.7.x / ddd4j 1.0.x to Boot 3.5.x / ddd4j 2.0.x).
- Auditing whether an existing project's Boot→ddd4j→JDK→Maven/POM tuple is internally consistent.
- Deciding whether Boot 4.0–4.1 targets are buildable with the current Maven toolchain (Maven 4 / POM 4.1 required).
- Proving that the selected line's artifacts are remotely consumable from the private repository, not just present in a local cache.
- Explaining why a proposed parent/BOM combination is incompatible with the current JDK or Maven model.

## When NOT to Use

Do not use this skill when:

- **The project is plain Spring Boot without ddd4j** — generic Java and Spring Boot skills apply; do not use this matrix to pick Boot versions for a non-ddd4j stack.
- **Maven version ownership spans multiple ddd4j products (parent/BOM authority)** — use `ddd4j-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-bom`.
- **The runtime is Javalin, Quarkus, or Spring Cloud, not ddd4j-boot** — use `ddd4j-javalin-version-selection`, `ddd4j-quarkus-version-selection`, or `ddd4j-cloud-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill <skill-name>`.
- **How a starter wires auto-configuration is the question** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The request is to mechanically rewrite source code after the line is chosen** — this skill selects and justifies the tuple; code migration itself should be planned with generic migration skills.
- **Unreleased coordinates or in-development versions are requested** — this skill should not guess versions; only the 13 published lines are selectable.

## Trigger Keywords

**English**: version selection, maintenance line, compatibility matrix, JDK mapping, Maven version, POM model, upgrade path

**中文**: 版本选择, 维护线, 兼容矩阵, JDK 对应, Maven 版本, POM 模型, 升级路径
## Quick Matrix

| Boot | ddd4j | JDK | Maven/POM |
|---|---|---:|---|
| 2.3–2.7 | 1.0.x | 8 | Maven 3 / 4.0 |
| 3.0–3.5 | 2.0.x | 17 | Maven 3 / 4.0 |
| 4.0–4.1 | 3.0.x | 21 | Maven 4 / 4.1 |

For exact patches, see the [13 Maintenance Lines](references/maintenance-matrix.md).

## Decision Rules

1. Existing projects first respect the current Spring Boot/JDK.
2. New projects choose the highest primary combination the organization supports and that is remotely consumable.
3. Do not mix parent/BOM across ddd4j main lines.
4. Boot 4 requires Maven 4/POM 4.1/subprojects.
5. Output SOURCE/TEST/CI/PUBLISHED/CONSUMED evidence status.

## Capability Boundaries

### ✅ Strong At

- Selecting among the 13 maintenance lines.
- Upgrade paths and incompatibility explanations.
- JDK/Maven/POM constraints.
- Remote consumption gates.

### ⚠️ Needs Input

- Spring Boot/JDK/Maven.
- Current parent/BOM.
- Private repository and CI requirements.

### ❌ Out of Scope

- Automatically upgrading source code.
- Guessing unreleased coordinates.
- Using a local cache to prove remote availability.

## Workflow

### Step 1: Collect the constraints

Gather the Spring Boot version, JDK, and Maven version from the current project (`git branch`, `java -version`, `./mvnw -version`). Record the current parent/BOM and whether the project is new, upgraded, or in maintenance.

### Step 2: Match the maintenance line

Read the 13-line matrix (`config/consistency/ddd4j-boot-build-matrix.tsv`) and output the complete Boot→ddd4j→JDK→Maven/POM tuple. Never select by branch name alone; the matrix and POM are the authority.

### Step 3: Verify the toolchain

Confirm the toolchain actually satisfies the tuple — Boot 4 targets require Maven 4, POM model 4.1, and subprojects. A mismatch here invalidates the selection before any build runs.

### Step 4: Prove the evidence

Build and test on the selected line, check CI status for the final SHA, and consume the artifact from the private repository with an isolated clean cache (`-U`). A warm local cache is not proof of availability.

### Step 5: Report the tuple and the gaps

Produce one report: selected line with rationale, incompatible and unverified items, evidence status (SOURCE/TEST/CI/PUBLISHED/CONSUMED), upgrade path steps when applicable, and missing inputs phrased as `missing: specific item; how to provide: path or configuration`.

## Gotchas

- A green local build does not prove remote availability — a warm cache hides the fact that the artifact was never published. Consume with an isolated clean cache (`-U`) before declaring CONSUMED.
- The branch name does not determine the line. Branch names and POMs disagree often enough that only `config/consistency/ddd4j-boot-build-matrix.tsv` plus the actual POM count as evidence.
- Java 8 cannot run Boot 3 lines, and Java 17 cannot currently run ddd4j 3.0.x — the latest-version-only instinct silently picks an unbuildable tuple.
- Boot 4 requires Maven 4 / POM 4.1 / subprojects. Bumping only the parent version still fails the build; the model version itself must move.
- Upgrading is not "bump the parent": the order JDK→Spring Boot→ddd4j→ddd4j-boot→Maven/POM is layered, and crossing main lines is not a version swap.
- When the matrix and real execution results conflict, the POMs and run results win — fix the matrix, do not force the code to match a stale TSV.

## Deep Reference

- [Maintenance Matrix](references/maintenance-matrix.md)
- [Selection and Upgrade](references/selection-and-upgrade.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output Maven settings or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-boot-version-selection` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-version-selection` to review existing usage against the current source."
- "Use `$ddd4j-boot-version-selection` to return an implementation choice, evidence state, and remaining risk."

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
