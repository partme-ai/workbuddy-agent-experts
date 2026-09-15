---
name: ddd4j-quarkus-version-selection
description: Use when choosing a ddd4j-quarkus 3.3.x or 4.0.x line based on ddd4j, Quarkus Platform, JDK, Maven, and POM model constraints. 中文触发词：版本选择、适配线、维护线、兼容矩阵、Quarkus Platform 对应、JDK 对应、Maven 版本、POM 模型、升级路径。
license: Apache-2.0
---

# ddd4j-quarkus Version Selection

## Overview

Covers uniformly: 3.3.x→ddd4j 2/JDK17/Maven3/Quarkus 3.37.4; 4.0.x→ddd4j 3/JDK21/Maven4/Quarkus 3.38.2, not split per artifact. Choose 3.3.x or 4.0.x first, then read the current source.

## When to Use

- Choosing the ddd4j-quarkus maintenance line for a new Quarkus service, given the Quarkus Platform, JDK, and Maven the organization supports.
- Auditing whether an existing project's Quarkus Platform→ddd4j→JDK→Maven/POM tuple is internally consistent.
- Planning an upgrade that crosses lines (3.3.x → 4.0.x means ddd4j 2.0.x → 3.0.x, JDK 17 → 21, and Maven 3 → 4 together).
- Explaining why a proposed combination is unbuildable — for example Maven 3 against the 4.0.x POM model.
- Confirming `quarkus-bom.version` and toolchain evidence before any extension or application work starts.
- Deciding whether code or configuration copied from the other line can be trusted before reading its source.

## When NOT to Use

Do not use this skill when:

- **The Quarkus project does not use ddd4j** — generic Java and Quarkus skills apply; do not use this matrix to pick Quarkus Platform versions for a non-ddd4j stack.
- **Spring Boot is the runtime** — use `ddd4j-boot-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-version-selection`.
- **Javalin is the runtime** — use `ddd4j-javalin-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-version-selection`.
- **Spring Cloud is the runtime** — use `ddd4j-cloud-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-version-selection`.
- **Maven parent or BOM ownership spans several ddd4j products** — use `ddd4j-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-bom`.
- **The line is already fixed and the question is module boundaries** — use `ddd4j-quarkus-architecture` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-architecture`.

## Trigger Keywords

**English**: version selection, adaptation line, maintenance line, compatibility matrix, Quarkus Platform mapping, JDK mapping, Maven version, POM model, upgrade path

**中文**: 版本选择, 适配线, 维护线, 兼容矩阵, Quarkus Platform 对应, JDK 对应, Maven 版本, POM 模型, 升级路径

## Core Scope

3.3.x→ddd4j 2/JDK17/Maven3/Quarkus 3.37.4; 4.0.x→ddd4j 3/JDK21/Maven4/Quarkus 3.38.2.

## Core Rules

1. 3.3.x and 4.0.x each keep their own ddd4j/JDK/Maven/POM/Quarkus contract.
2. 4.0.x is the adapter line name and does not mean Quarkus Platform 4.
3. CDI/Arc, runtime/deployment, and BuildItem/Recorder are not explained with the Spring model.
4. Bean scope, request Context, startup/shutdown, and native boundaries are explicit.
5. Report source, tests, CI, Security, and publishing in layers.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for version selection and Quarkus adaptation.
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

### Step 1: Collect the constraints

Gather the target Quarkus Platform version, JDK, and Maven from the project (`git branch`, `java -version`, `./mvnw -version`), and record the branch, root POM model, and wrapper version before quoting any line contract.

### Step 2: Match the maintenance line

3.3.x maps to ddd4j 2 / JDK 17 / Maven 3 / Quarkus Platform 3.37.4; 4.0.x maps to ddd4j 3 / JDK 21 / Maven 4 / Quarkus Platform 3.38.2. Confirm the platform version from `quarkus-bom.version`, never from the line name — 4.0.x is an adapter line name, not Quarkus Platform 4.

### Step 3: Verify the toolchain

Run the toolchain checks and confirm the POM model matches the line contract. A toolchain mismatch (for example Maven 3 against the 4.0.x POM model) invalidates the selection before any build runs.

### Step 4: Verify the evidence

Build and run the line's tests (JVM and, where applicable, native), check CI for the final SHA, and consume artifacts from the private repository with a clean cache. A warm local cache is not evidence of availability.

### Step 5: Report the tuple and the gaps

Produce a single report: the selected line with the complete tuple, verification commands and evidence state per tier, incompatible and unverified items, and missing inputs phrased as `missing: specific item; how to provide: path or configuration`.

## Gotchas

- `4.0.x` is the ddd4j-quarkus maintenance-line name — it does not mean Quarkus Platform 4. Both lines sit on Quarkus Platform 3.x (3.37.4 and 3.38.2); the platform version must be read from `quarkus-bom.version`.
- Maven 3 cannot build the 4.0.x POM model, and JDK 17 cannot run ddd4j 3.0.x — the Maven/JDK versions are part of the line contract, not local preferences.
- A BOM import does not mean the runtime bean is assembled — build items and recorders do the wiring, so a correct version tuple alone proves nothing at runtime.
- CDI bean discovery in Quarkus is build-time: a class present in source without a bean-defining annotation produces no bean, and Arc reports it as a build failure, not a runtime lookup miss.
- Quarkus extensions are a runtime/deployment module pair; picking an artifact by groupId alone can silently omit the deployment module that holds the build steps.
- Branch names and POMs disagree often enough that only the root POM plus `git branch`, `java -version`, and `./mvnw -version` output count as toolchain evidence.

## Output and Exceptions

When input is missing, output "missing: target line/extension/runtime; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, OIDC secrets, or database, broker, or private repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例仅使用脱敏的虚构版本信息。

## Quick Start

- "Use `$ddd4j-quarkus-version-selection` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-quarkus-version-selection` to review existing usage against the current source."
- "Use `$ddd4j-quarkus-version-selection` to return an implementation choice, evidence state, and remaining risk."

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
