---
name: ddd4j-version-selection
description: Use when choosing compatible ddd4j, ddd4j-boot, ddd4j-cloud, ddd4j-javalin, or ddd4j-quarkus versions for a new project, upgrade, migration, or maintained release line. 中文触发词：版本选择、兼容矩阵、JDK 对应、Maven 版本、POM 模型、升级路径、维护线、Boot 版本。
license: Apache-2.0
---

# ddd4j Version Selection

## Overview

What gets selected is a complete compatibility tuple, not a single "latest version". Fix the JDK, build tool, and runtime first, then choose ddd4j and the adapter project.

## When to Use

- Starting a new project: pick the ddd4j line plus adapter project from JDK and runtime constraints.
- Planning an upgrade or migration across maintenance lines (1.0.x / 2.0.x / 3.0.x).
- Matching Spring Boot, Spring Cloud, Javalin, or Quarkus versions to a ddd4j line.
- Deciding on the Maven 3 / POM 4.0 vs Maven 4 / POM 4.1 toolchain boundary.
- Verifying that a chosen combination is remotely consumable (private Maven metadata, clean-cache resolve).
- Producing a graded answer: recommended, alternative, incompatible, unverified.

## When NOT to Use

Do not use this skill when:

- **Governance inside a chosen line is the question** — parent/dependencies/BOM ownership, import order, effective POM — use `ddd4j-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-bom`.
- **Runtime wiring after the versions are fixed is the question** — use `ddd4j-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-runtime`.
- **Code changes required by the migration are the question** (API adaptation on the target line) — use `ddd4j-core` or the relevant dimension skill instead; Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **A request asks to guess that an unreleased version works, or to substitute branch names for POM/CI/remote evidence** — do not use this skill to bless that; unverified claims are output as unverified, not as recommendations.
- **Generic Spring Boot / Quarkus / Javalin version advice with no ddd4j involvement** — use the framework's own resources; this skill only adjudicates ddd4j-compatible tuples.

## Trigger Keywords

**English**: version selection, compatibility matrix, JDK mapping, Maven version, POM model, upgrade path, maintenance line, Boot version

**中文**: 版本选择, 兼容矩阵, JDK 对应, Maven 版本, POM 模型, 升级路径, 维护线, Boot 版本

## Quick Start

- "Which ddd4j line should a JDK 17 Spring Boot 3.4 project pick?"
- "Can Javalin 7.1 use ddd4j 3.0.x?"
- "Which Boot and ddd4j versions correspond to Spring Cloud 2024.0.x?"
- "Why does Quarkus 4.0.x still use Quarkus 3.38?"

## Input Contract

Collect at least:

1. Whether the project is new, an upgrade, or maintenance.
2. Available JDK and Maven versions.
3. Target Spring Boot/Cloud, Javalin, or Quarkus versions.
4. Whether POM 4.0/Maven 3 is mandatory.
5. Whether remote SNAPSHOT consumption and verified CI are required.

When input is missing, give a tentative candidate first, then output "missing: specific constraint; how to provide: supply the POM, java -version, mvn -version".

## Decision Order

### Step 1: Lock the ddd4j main line by JDK

Map the available JDK to the line: Java 8 → 1.0.x, Java 17 → 2.0.x, Java 21 → 3.0.x. No other constraint overrides the JDK.

### Step 2: Lock the adapter project maintenance line by runtime

Match the runtime (Spring Boot/Cloud, Javalin, Quarkus) to its adapter project line — e.g. Boot 3.4 → ddd4j-boot 3.4.x, Javalin 7.1 → ddd4j-javalin 7.1.x, Quarkus Platform 3.38 → ddd4j-quarkus 4.0.x.

### Step 3: Verify the Maven / POM Model

Confirm the toolchain: 1.x/2.x lines are Maven 3 / POM 4.0; the 3.x line is Maven 4 / POM 4.1. Read it from the target POM, not from the line name.

### Step 4: Verify the exact upstream framework version

Check the concrete framework version (Boot parent, Cloud train, Javalin, Quarkus Platform) against the compatibility matrix — re-reading the current POMs, not a remembered table.

### Step 5: Query private Maven repository metadata

Check the remote coordinates and final SHA for the chosen versions. If remote resolution cannot be verified, mark it NOT VERIFIED — do not silently assume availability.

### Step 6: Output the four categories

Return recommended, alternative, incompatible, and unverified combinations, each with its rationale and evidence status (SOURCE / TEST / CI / PUBLISHED / CONSUMED).

## Quick Matrix

| ddd4j | JDK | Maven/POM | Boot |
|---|---:|---|---|
| 1.0.x | 8 | Maven 3 / 4.0.0 | Boot 2.3–2.7 |
| 2.0.x | 17 | Maven 3 / 4.0.0 | Boot 3.0–3.5 |
| 3.0.x | 21 | Maven 4 / 4.1.0 | Boot 4.0–4.1 |

For the full Boot, Cloud, Javalin, and Quarkus matrices, see the [Compatibility Matrix](references/compatibility-matrix.md).

## Output Format

| Field | Content |
|---|---|
| Recommended combination | JDK, Maven, POM, ddd4j, adapter project, framework |
| Selection rationale | Matched source matrix and constraints |
| Incompatible items | Conflicting fields and reasons |
| Evidence status | SOURCE / TEST / CI / PUBLISHED / CONSUMED |
| Follow-up verification | Exact commands, branches, and coordinates |

## Capability Boundaries

### ✅ Strong At

- Version combination selection across the five repositories.
- The Maven 3/4 and POM 4.0/4.1 boundary.
- Primary combinations, compatible alternatives, and upgrade paths.
- Distinguishing local success from remote consumability.

### ⚠️ Needs Input

- Current POM, branch, or target framework version.
- Private repository access conditions.
- Whether historical lines may upgrade JDK/Maven.

### ❌ Out of Scope

- Guessing that unreleased versions work.
- Automatically upgrading dependencies or switching branches.
- Substituting branch names for POM, CI, and remote evidence.

## Gotchas

- Recommending the highest ddd4j main line to every project — a Java 8 shop handed 3.0.x gets a build that cannot even compile; the JDK locks the line before ambition does.
- Promoting Javalin 7.1.x to Maven 4 — the Javalin 7.1.x adapter line stays Maven 3 / POM 4.0; only 7.2.x crossed to Maven 4 / POM 4.1, and the difference is invisible in the line names.
- Treating the ddd4j-quarkus `4.0.x` line as Quarkus Platform 4 — it pairs with Quarkus Platform 3.38.2; the adapter line number and the platform version are unrelated scales.
- Reading only the Spring Cloud branch name without checking the Boot parent — `2024.0.x` says nothing until the Boot parent (3.4.x) and its ddd4j line (2.0.x) are confirmed underneath.
- Treating the start of a deploy upload as a finished release — a local build or an upload-in-progress is not remotely consumable; only a clean-cache remote resolve proves it.
- Writing Security SKIPPED down as PASS — an unrun verification stage recorded as passed is indistinguishable from a real one in the release notes.
- Copying a compatibility table without a date or SHA — matrices go stale; re-read the current POMs and verification scripts every time the question is asked.

## Deep Reference

- [Compatibility Matrix](references/compatibility-matrix.md)
- [Evidence and Gates](references/evidence-and-gates.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Maven settings, tokens, passwords, or credentialed private repository URLs; report only credential sources and redacted errors. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；仓库地址与错误信息仅以脱敏形式输出。

## Audience and Customization

- New project developers provide the JDK and target runtime.
- Maintainers provide the existing POM, branch, and upgrade constraints.
- Release engineers specify CI/private repository/clean-cache evidence requirements.

Customize the target product, allowed maintenance lines, and evidence level. When input is insufficient, give a tentative combination first, then list "missing: version constraints; how to provide: supply the POM and tool versions".

## FAQ

1. **Is the latest version always chosen?** No — constraints come first.
2. **Is picking just the ddd4j version enough?** No — the full tuple is required.
3. **Can a branch name prove the framework version?** No.
4. **Does a local SNAPSHOT count as available?** It is not remotely available.
5. **What if CI never started?** Mark BLOCKED.
6. **What if the matrix is stale?** Refresh the current POMs and verification scripts.
