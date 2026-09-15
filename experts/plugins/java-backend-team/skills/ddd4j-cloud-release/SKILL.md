---
name: ddd4j-cloud-release
description: Use when validating, publishing, or remotely consuming all ddd4j-cloud maintenance lines, including upstream Boot and ddd4j artifacts, Maven 3 or 4, private repository recovery, and clean-cache proof. 中文触发词：发布验证、八条维护线、私有仓库、空缓存消费、上游可用性、CI 检查、Maven 版本。
license: Apache-2.0
---

# ddd4j-cloud Release

## Overview

Covers the eight-line serial build, upstream Boot/ddd4j, Maven 3/4, private repository recovery, remote metadata, and clean-cache consumption uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Validating the eight-line serial build with each line's Maven 3/4 and JDK contracts.
- Checking upstream availability: the Boot and ddd4j artifacts each line needs must exist remotely.
- Publishing to the private repository — only after explicit authorization, with zero exit and complete remote metadata.
- Exercising private repository recovery where the contract requires it.
- Proving remote availability with isolated clean-cache consumption (`-U`).
- Recording exact Git SHAs and evidence grading per line for a release report.

## When NOT to Use

Do not use this skill when:

- **Designing or running the test suites themselves is the question** — use `ddd4j-cloud-testing` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-testing`.
- **Which Cloud→Boot→ddd4j combination to publish is the question** — use `ddd4j-cloud-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-version-selection`.
- **A BOM import-order fix is needed before the release** — use `ddd4j-cloud-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-bom`.
- **The lines are ddd4j-boot, ddd4j-javalin, or ddd4j-quarkus lines** — use `ddd4j-boot-release`, `ddd4j-javalin-release`, or `ddd4j-quarkus-release` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-release` (or the matching release skill).
- **Generic Maven release/deploy without ddd4j** — do not use this skill; apply generic Maven release tooling instead (no install command).
- **Deploying released services into production is the goal** — do not use this skill; production rollout is out of scope here, this skill stops at published, verified artifacts.

## Trigger Keywords

**English**: release validation, eight maintenance lines, serial build, private repository, clean-cache consumption, remote metadata, upstream availability, publish authorization

**中文**: 发布验证, 八条维护线, 私有仓库, 空缓存消费, 远端元数据, 上游可用性, 发布授权, CI 检查

## Core Scope

Eight-line serial build, upstream Boot/ddd4j, Maven 3/4, private repository recovery, remote metadata, clean-cache consumption.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for release work and Spring Cloud integration.
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

Run `ddd4j-cloud-version-selection` to fix the combinations for the eight lines, then record each checkout's Git SHA and confirm clean worktrees.

### Step 2: Verify upstream availability

Confirm the required Boot and ddd4j artifacts exist remotely for each line. Classify anything missing as BLOCKED(upstream).

### Step 3: Build serially

Build all eight lines serially, each with its own Maven 3/4 and JDK contracts, then run the compatibility scripts and verification consumers.

### Step 4: Publish and recover

Deploy to the private repository only after explicit authorization; require zero exit and complete remote metadata. Exercise private repository recovery where the contract requires it, and prove remote availability with isolated clean-cache consumption (`-U`).

### Step 5: Report the release

Output per-line build, publish, metadata, and consumption results; evidence grading per tier with exact SHAs; the BLOCKED/SKIPPED inventory and remaining risks; redacted errors only.

## Gotchas

- Publishing without explicit user authorization is forbidden — validation is read-only until the deploy is authorized, and a green pipeline is not authorization.
- A zero deploy exit code does not prove completeness — the remote metadata must actually list every artifact before consumption can be claimed.
- A warm local repository hides upstream and metadata gaps: proof requires isolated clean-cache consumption with `-U`, never the release machine's cache.
- Each line pins its own Maven 3/4 and JDK contract — building all eight lines with one toolchain produces silently different artifacts.
- The release contract is a serial eight-line build; running lines concurrently interleaves private-repository state and invalidates the evidence trail.
- Upstream gaps must be reported BLOCKED(upstream), never patched by uploading hand-made artifacts to the private repository.
- Private-repository errors can embed credentials — always redact before any output.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或私钥；发布日志与错误信息仅以脱敏形式输出。

## Quick Start

- "Use `$ddd4j-cloud-release` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-release` to review existing usage against the current source."
- "Use `$ddd4j-cloud-release` to return an implementation choice, evidence state, and remaining risk."

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
