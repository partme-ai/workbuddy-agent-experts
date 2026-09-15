---
name: ddd4j-boot-bom
description: Use when managing ddd4j-boot parent, dependencies, BOM imports, effective POMs, version ownership, Spring Boot dependency alignment, Maven model, or consumer coordinates. 中文触发词：版本所有权、BOM 导入、effective POM、依赖管理、parent POM、导入顺序、版本对齐。
license: Apache-2.0
---

# ddd4j-boot BOM

## Overview

Targets the current ddd4j-boot maintenance line: boot-parent, boot-dependencies, boot-bom, the Spring Boot BOM, the ddd4j BOM, and effective POMs. Confirm the version line first, then apply this skill.

## When to Use

- Deciding which POM owns a version: `ddd4j-boot-parent`, `ddd4j-boot-dependencies`, `ddd4j-boot-bom`, or a concrete module.
- Verifying Spring Boot BOM and ddd4j BOM import order through an effective POM (`mvn help:effective-pom`).
- Cleaning up concrete modules that re-pin versions already managed by the BOM.
- Aligning third-party dependency versions with the Spring Boot ecosystem on a specific Boot line (2.3–4.1).
- Explaining why a dependency resolved to an unexpected version on the current line.
- Reviewing the Boot 4 lines' Maven 4 / POM 4.1 model requirements before consumer projects upgrade.

## When NOT to Use

Do not use this skill when:

- **Version ownership spans multiple ddd4j products (the top-level parent and ddd4j-dependencies)** — use `ddd4j-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-bom`.
- **You are choosing which Boot/JDK/Maven line to adopt** — use `ddd4j-boot-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-version-selection`.
- **Module boundaries or starter responsibilities are the question** — use `ddd4j-boot-architecture` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-architecture`.
- **The BOM question concerns the Cloud or Quarkus products, not ddd4j-boot** — use the matching `ddd4j-cloud-*` or `ddd4j-quarkus-*` skill instead; do not apply the Boot BOM layout to them.
- **A runtime bean or auto-configuration problem is suspected** — dependency management should not be debugged as if it were wiring; use `ddd4j-boot-autoconfiguration`.
- **The project is plain Spring Boot without ddd4j** — generic Spring Boot / Maven skills apply; this skill's ownership rules assume the ddd4j POM hierarchy.

## Trigger Keywords

**English**: version ownership, BOM imports, effective POM, dependency management, parent POM, import order, version alignment

**中文**: 版本所有权, BOM 导入, effective POM, 依赖管理, parent POM, 导入顺序, 版本对齐
## Core Scope

boot-parent, boot-dependencies, boot-bom, Spring Boot BOM, ddd4j BOM, effective POM.

## Rules

1. Ordinary third-party versions are governed by ddd4j-dependencies; the Boot layer only overrides the Boot ecosystem.
2. BOM import order must be verified with an effective POM.
3. Boot 4 uses Maven 4/POM 4.1.
4. Concrete modules must not re-pin already-managed versions.
5. parent/BOM/aggregator POMs are different responsibilities.

## Capability Boundaries

### ✅ Strong At

- Boot-specific architecture and configuration decisions for the current line.
- Choosing among multiple implementations and dividing responsibilities.
- Maintenance-line differences and verification paths.

### ⚠️ Needs Input

- Target Boot line, JDK, Maven, and POM.
- Target module and runtime behavior.
- Current source/tests/CI status.

### ❌ Out of Scope

- Rewriting ddd4j core domain contracts.
- Treating dependency presence as runtime success.
- Automatically releasing or upgrading production projects.

## Workflow

### Step 1: Confirm the source of truth

Run `ddd4j-boot-version-selection` to fix the line, JDK, Maven, and POM model, then read `ddd4j-boot-parent/pom.xml`, `ddd4j-boot-dependencies/pom.xml`, and `ddd4j-boot-bom/pom.xml` on that line.

### Step 2: Verify version ownership

Confirm ordinary third-party versions live in ddd4j-dependencies and that the Boot layer only overrides the Boot ecosystem. Flag any concrete module that re-pins an already-managed version — it should be returned to the BOM.

### Step 3: Verify the import order

Build the effective POM (`mvn help:effective-pom`) and confirm the Spring Boot BOM and ddd4j BOM imports resolve in the intended order. Import order is only provable in the effective POM, never by reading source POMs.

### Step 4: Validate the build

Run the target module build and tests on the selected line and check CI status for the final SHA. A BOM change that compiles locally may still break consumers who import the BOM.

### Step 5: Report ownership and evidence

Produce one report: version line, effective-POM findings, the version ownership map (who manages which coordinates), import-order confirmation, tests and CI evidence per layer, and each violation with a proposed fix.

## Gotchas

- Import order in source POMs proves nothing — two BOM imports that "look right" resolve differently than they read. Only the effective POM shows the winning version.
- A concrete module re-pinning a managed version often builds fine locally and diverges silently for consumers; dependency overreach is invisible until someone imports the BOM.
- Ordinary third-party versions are governed by ddd4j-dependencies; overriding them in the Boot layer "because it builds" breaks the ownership contract even when resolution succeeds.
- parent, BOM, and aggregator POMs are different responsibilities with different consumers; merging them looks like simplification and breaks granular imports.
- The Boot 4 lines change the Maven model itself (Maven 4 / POM 4.1), so a BOM that works on 3.5.x cannot be assumed valid on 4.x.
- Dependency management fixing a version is not evidence the feature works — resolution success and bean creation are different layers.

## Output and Exceptions

Output the version line, modules, configuration entry points, default implementations, override points, tests, and risks. When input is missing, write "missing: target line or module; how to provide: supply the POM and behavior requirements".

## Deep Reference

- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output settings, tokens, passwords, or production connection information. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例仅使用脱敏的虚构坐标。

## Quick Start

- "Use `$ddd4j-boot-bom` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-bom` to review existing usage against the current source."
- "Use `$ddd4j-boot-bom` to return an implementation choice, evidence state, and remaining risk."

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
