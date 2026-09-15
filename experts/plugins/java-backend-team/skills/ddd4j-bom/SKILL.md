---
name: ddd4j-bom
description: Use when choosing or changing ddd4j parent, dependencies, BOM imports, Maven model, version ownership, dependency properties, release-line alignment, or consumer dependency management. 中文触发词：版本所有权、BOM 导入、effective POM、Maven 模型、依赖管理、空缓存消费、发布验证。
license: Apache-2.0
---

# ddd4j BOM and Maven Governance

## Overview

`parent` owns the build, `dependencies` owns third-party versions, `BOM` owns ddd4j consumer coordinates. The three have distinct responsibilities. Adapter-project BOMs own only their own ecosystem versions.

## When to Use

- Deciding whether a change belongs in `ddd4j-parent`, `ddd4j-dependencies`, or the `ddd4j-bom`.
- Adding a new module or property and keeping versions out of concrete module POMs.
- Migrating or checking the Maven model: POM 4.0 `<modules>` vs POM 4.1 `<subprojects>`, Maven 3 vs Maven 4.
- Diagnosing version conflicts caused by BOM import order or property leakage.
- Verifying that a published line is actually consumable from a clean local repository.
- Aligning dependency properties across the 1.0.x, 2.0.x, and 3.0.x lines.

## When NOT to Use

Do not use this skill when:

- **Choosing which ddd4j line or adapter project a new project should adopt is the question** — use `ddd4j-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-version-selection`.
- **Runtime wiring after the artifacts resolve is the question** — use `ddd4j-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-runtime`.
- **Application code has a compile or runtime problem unrelated to Maven governance** — use the generic `java-skills` or the relevant dimension skill; a build governance skill does not debug business code.
- **The request is to silently bump versions, force-publish, or skip the enforcer** — do not use this skill for that; silent version changes and publishing require explicit authorization.
- **A single downstream project's internal dependency hygiene is the question** (not ddd4j governance) — generic Maven guidance applies instead.

## Trigger Keywords

**English**: version ownership, BOM import, effective POM, Maven model, dependency management, clean-cache consumption, release verification, maintenance line

**中文**: 版本所有权, BOM 导入, effective POM, Maven 模型, 依赖管理, 空缓存消费, 发布验证, 维护线

## Quick Selection

| Need | Use |
|---|---|
| Plugin, compile, and publish defaults | `ddd4j-parent` |
| Third-party `dependencyManagement` | `ddd4j-dependencies` |
| Business consumer imports ddd4j module versions | `ddd4j-bom` |
| Boot / Javalin / Quarkus / Cloud specific versions | Corresponding adapter-project `dependencies` / BOM |

## Core Rules

1. `1.0.x` / `2.0.x` stay on POM 4.0 / Maven 3. `3.0.x` uses POM 4.1 / Maven 4.
2. POM 4.0 uses `<modules>` / `<module>`. POM 4.1 uses `<subprojects>` / `<subproject>`.
3. Concrete modules must not duplicate third-party versions already managed by `dependencies`.
4. `ddd4j-dependencies` is the authoritative platform dependency source.
5. Boot / Cloud / Javalin / Quarkus BOMs manage only their own ecosystem surface.
6. BOM import order affects the effective version — always check the effective POM.
7. A resolvable parent / BOM does not mean every JAR is published.

## Capability Boundaries

### ✅ Strong At

- Choosing between `parent`, `dependencies`, and BOM responsibilities.
- Maven 3 / 4 and Model 4.0 / 4.1 differences.
- Property layout, version leakage, and import conflicts.
- Aligning dependencies across multiple maintenance lines and verifying consumption.

### ⚠️ Needs Input

- Current maintenance line and JDK / Maven versions.
- Target POM and effective POM.
- Private / central Maven resolution results.

### ❌ Out of Scope

- Silently changing versions or publishing.
- Using `enforcer.skip` as proof of release.
- Inferring ownership from XML keywords alone.

## Validation Gates

- `scripts/test_maven4_model_contract.py`
- `scripts/test_dependency_property_layout.py`
- `scripts/test_bom_import_conflicts.py`
- `scripts/test_dependency_alignment.py`
- `scripts/check-bom-alignment.sh`
- Clean-cache consumer `dependency:go-offline` / `compile`

## Workflow

### Step 1: Decide the scope and ownership

Identify whether the change touches `parent` (build/plugin conventions), `dependencies` (third-party versions), or the `BOM` (consumer-facing ddd4j coordinates), and confirm the maintenance line's JDK / Maven / POM Model contract. Edit only the file that owns the change.

### Step 2: Make the model-correct edit

Use `<modules>` / `<module>` on POM 4.0 lines and `<subprojects>` / `<subproject>` on the Maven 4 / POM 4.1 line. Never pin a third-party version inside a concrete module that `ddd4j-dependencies` already manages.

### Step 3: Run the validation gates

Execute the model-contract, property-layout, import-conflict, and alignment scripts (`scripts/test_maven4_model_contract.py`, `test_dependency_property_layout.py`, `test_bom_import_conflicts.py`, `test_dependency_alignment.py`, `check-bom-alignment.sh`).

### Step 4: Verify consumption on a clean cache

Generate `help:effective-pom` in a consumer project, then run `dependency:go-offline` and `compile` with `-U` against an empty local repository. A warm cache hides missing artifacts, so the clean-cache resolve is the real gate.

### Step 5: Report with evidence grades

Report the maintenance line, JDK, Maven, POM Model, changed ownership, effective-POM excerpts, script outputs, and the consumption result — each tagged SOURCE / TEST / CI / PUBLISHED / CONSUMED.

## Gotchas

- Mixing BOM and parent responsibilities — plugin and build config placed in a BOM looks harmless until a consumer imports the BOM and inherits build behavior it never asked for.
- Scattered numeric versions inside concrete modules — each pin silently overrides `ddd4j-dependencies`, and the effective version depends on declaration order rather than the platform.
- Keeping `<modules>` in a Maven 4 aggregator — POM 4.1 dropped it for `<subprojects>`; the element is ignored or fails depending on the Maven build, not the source.
- Reading only the source POM — BOM import order and parent chains rewrite versions; the effective POM is the only truth about what a consumer actually gets.
- Claiming a full release after partial upload — "the deploy started" and "the artifacts are consumable" are different claims; only a clean-cache resolve proves the latter.
- A warm private-repository cache masking missing parent / BOM artifacts — CI resolves fine locally and fails only on a machine that has never seen the artifacts.

## Output and Exceptions

Return `maintenance line, JDK, Maven, POM Model, version owners, effective POM, and consumption state`. When missing, return `missing: effective model or remote coordinate; how to provide: run help:effective-pom or a clean-cache resolve`.

## Deep Reference

- [Ownership and Imports](references/ownership-and-imports.md)
- [Maven Model](references/maven-model.md)
- [Publication and Consumption](references/publication-and-consumption.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never print `settings.xml`, server passwords, or private-repository tokens. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；仓库地址与认证信息仅以脱敏形式输出。

## Quick Start

- "Use `$ddd4j-bom` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-bom` to review existing usage against the current source."
- "Use `$ddd4j-bom` to return an implementation choice, evidence state, and remaining risk."

## Audience and Customization

- Developers: provide the target maintenance line, POM, capabilities, and acceptance behavior.
- Architects: specify a read-only boundary, compatibility, or migration review.
- Testers / release engineers: specify the required evidence levels; do not auto-expand to release or production operations.

Customize the target framework, allowed implementations, excluded modules, compatibility requirements, and evidence level. When input is insufficient, give a tentative verdict first, then list `missing: specific item; how to provide: path or configuration`.

## FAQ

1. **Are skills organized by Maven artifact?** No — by the user-facing capability domain.
2. **Can I copy another maintenance line directly?** No — verify the version and source first.
3. **Does a class existing in source prove the capability works?** No — registration and behavior evidence are also required.
4. **How do I report tests that did not run?** Mark `NOT RUN` or `BLOCKED`.
5. **Can the skill commit or release automatically?** Only after explicit user authorization.
6. **What if the implementation is missing?** Describe the missing module or evidence; do not invent APIs.
