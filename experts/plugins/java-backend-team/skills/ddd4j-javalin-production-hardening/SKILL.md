---
name: ddd4j-javalin-production-hardening
description: Use when hardening or releasing ddd4j-javalin 6.7.x, 7.1.x, or 7.2.x across runtime lifecycle, readiness, configuration, idempotency, CORS, multi-branch TDD, CI, or private Maven workflows. 中文触发词：生产加固、多分支、TDD、CI 门禁、私有 Maven 发布、就绪检查、幂等、CORS。
license: Apache-2.0
---

# DDD4J Javalin Production Hardening

## Purpose

Turn a `ddd4j-javalin` hardening request into an evidence-backed delivery without collapsing review, planning, implementation, CI, publication, and production acceptance into one status.

## When to Use

- Reviewing production-readiness gaps across the three Javalin branches (`feature/6.7.x`, `feature/7.1.x`, `feature/7.2.x`) against their line contracts — 6.7.x → Javalin 6.7/ddd4j 1/JDK 17/Maven 3; 7.1.x → Javalin 7.1/ddd4j 2/JDK 17/Maven 3; 7.2.x → Javalin 7.2/ddd4j 3/JDK 21/Maven 4.
- Updating an approved specification or Superpowers plan and then executing it contract-first (TDD), with review, plan approval, and implementation kept as separate states.
- Carrying one approved behavior change across all three maintenance lines while preserving each line's toolchain and Javalin 6/7 API differences.
- Hardening runtime lifecycle, readiness, configuration validation, idempotency, or CORS where evidence tiers must stay separate.
- Inspecting CI on the three branches and executing an explicitly authorized private Maven release with remote-consumer proof.
- Verifying — challenging — claimed evidence without pushing or publishing.

## When NOT to Use

Do not use this skill when:

- **One capability is needed in depth (runtime, auth, data, web, mq, cache, testing, or release)** — use the matching `ddd4j-javalin-*` capability skill such as `ddd4j-javalin-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-runtime`.
- **The maintenance line itself must be chosen or matched** — use `ddd4j-javalin-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-version-selection`.
- **Core domain or SPI contracts are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Generic ddd4j Boot, Quarkus, or Cloud release work is the question (without a verified Javalin dependency blocker)** — use `ddd4j-boot-release`, `ddd4j-quarkus-release`, or `ddd4j-cloud-release` instead, for example Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-release`.
- **The project is plain Javalin or generic Java without ddd4j** — do not use this skill; use `java-skills` instead, since no ddd4j branch matrix or delivery gates apply.
- **Silently initializing Spec Kit/OpenSpec, creating a second specification, changing GitHub billing, or rotating secrets is what is being asked** — these are out of scope by design; surface them as decisions for the user instead.

## Trigger Keywords

**English**: production hardening, multi-branch, TDD, CI gates, private Maven release, readiness, idempotency, CORS

**中文**: 生产加固, 多分支, TDD, CI 门禁, 私有 Maven 发布, 就绪检查, 幂等, CORS

## Quick start

Typical requests:

- "Use `$ddd4j-javalin-production-hardening` to review the production-readiness gaps of the three Javalin branches and update the existing plan."
- "Complete runtime/readiness/CORS hardening with TDD according to the approved Phase D plan."
- "Check CI on the three branches, publish to the Alibaba Cloud private Maven repository, and finish with a clean-cache consumption verification."

Start by locating the real repository and reading current evidence. Do not assume the historical branch matrix, plan state, remote state, or credentials are still current.

## Capability boundaries

### Good fit

- Review Javalin runtime/bootstrap, lifecycle, readiness, configuration, CORS, idempotency, persistence, and shutdown behavior.
- Update an existing approved Javalin specification or Superpowers plan, then execute it with failing contracts first.
- Carry one approved behavior change across the three maintenance lines while preserving line-specific toolchains.
- Inspect GitHub Actions and execute an explicitly authorized private Maven release with remote-consumer proof.

### Needs project evidence or authorization

- Implementation needs the repository, current branch/worktree state, applicable instructions, and the active plan/specification.
- Push, branch switching, commit, private publication, or credential use needs the corresponding user authorization.
- Production claims need runtime/operational evidence; source and test results alone are insufficient.

### Out of scope

- Generic `ddd4j`, Boot, Quarkus, or Cloud release work unless it is a verified Javalin dependency blocker.
- Silently initializing Spec Kit/OpenSpec, creating a second specification, changing GitHub billing, or rotating secrets.
- Treating a CI start, artifact upload, HTTP 200, or local build as production acceptance.

## Required discovery

Before edits, report the SDD state and perform read-only discovery:

### Step 1: Resolve repository truth

Resolve the exact repo root and target module; inspect `git status --short --branch`, `git worktree list`, local/remote refs, and dirty files.

### Step 2: Read instructions and fact sources

Read applicable `AGENTS.md`, `CLAUDE.md`, README, branch/POM matrix, and the current specification, plan, tasks, and status report.

### Step 3: Detect the active SDD system

Detect `.specify/`, `openspec/`, and `docs/superpowers/{specs,plans}`. Continue the existing fact source. If both Spec Kit and OpenSpec are active for the same change and ownership is unclear, stop before creating artifacts and ask the user to choose.

### Step 4: Query the code graph before grep

If `.codegraph/` exists, use CodeGraph before grep for runtime entrypoints, lifecycle ownership, readiness contributors, and shutdown call paths.

### Step 5: Re-derive the branch contract

Re-derive the current branch contract from POMs, wrappers, CI workflows, and tests. Historical defaults are only hypotheses:

| Line | Expected dependency line | Expected Javalin | Toolchain hypothesis |
|---|---|---|---|
| `feature/6.7.x` | ddd4j 1.0.x | 6.7.0 | JDK 17, Maven 3, POM 4.0/modules |
| `feature/7.1.x` | ddd4j 2.0.x | 7.1.0 | JDK 17, Maven 3, POM 4.0/modules |
| `feature/7.2.x` | ddd4j 3.0.x | 7.2.3 | JDK 21, Maven 4, POM 4.1/subprojects |

Read [references/workflow.md](references/workflow.md) before planning or implementation. Read [references/release-gates.md](references/release-gates.md) before CI, push, deploy, or release-status work.

## Audience, routing, and customization

- Maintainers use review mode to audit production gaps and current plan truth without modifying code.
- Implementers use execution mode only after the plan is approved; it follows contract-first TDD and per-line adaptation.
- Release engineers use release mode for final-SHA CI inspection, serial private publication, and isolated consumption proof.
- Reviewers use verification mode to challenge claimed evidence without pushing or publishing.

Infer the mode from the request. If multiple modes are requested, preserve the order `review → plan approval → execute → verify → release`. Accept user constraints such as target branches, excluded modules, required CI jobs, private repository name, security-waiver status, and whether commit/push/deploy are authorized. These parameters override historical defaults but not current repository evidence or safety boundaries.

When required material is missing, report it as "missing: specific project/branch/specification/authorization/credential source; how to provide: state the path or authorization scope". Continue all safe read-only checks and give a provisional result instead of returning an empty response.

## Decision rules

- Keep the request Javalin-only. Escalate an upstream dependency only when current evidence proves it blocks Javalin.
- Review first. If the user says "write the plan first, execute later", update the existing plan and pause implementation until plan approval is explicit.
- Do not copy code mechanically across lines. Preserve Javalin 6 versus 7 APIs, Java syntax, Maven model, and dependency contracts.
- Convert each risk into an observable contract: fail first, implement the smallest behavior, then run focused and affected regression tests.
- Keep evidence tiers separate: source review → focused tests → per-line clean reactor → runtime/container tests → Git/remote SHA → CI → private publication → isolated remote consumption → production acceptance.
- Never expose repository credentials, settings files, tokens, private URLs containing secrets, or raw environment values. Report only credential presence/source and redact sensitive output.
- 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；证据输出仅报告凭据来源并脱敏，示例仅使用脱敏的虚构数据。

## Capability skill routing

Detailed implementations are handed off separately to `ddd4j-javalin-runtime`, `ddd4j-javalin-auth`, `ddd4j-javalin-data`, `ddd4j-javalin-web`, `ddd4j-javalin-mq`, `ddd4j-javalin-cache`, `ddd4j-javalin-testing`, and `ddd4j-javalin-release`. This skill retains only cross-capability review, plan approval, TDD orchestration, and production release gates.

## Hardening model

Investigate these concerns when relevant; do not force them into unrelated work:

- `Ddd4jJavalinRuntime`: coherent `start → validate → initialize → ready → drain → close`, rollback after partial initialization, and idempotent close.
- `JavalinLifecycleParticipant`: ordered initialization, readiness contribution, reverse-order shutdown, and clear required-versus-optional dependency semantics.
- Real configuration loading and startup validation instead of default-object construction plus port parsing.
- Aggregated readiness for dependencies such as database, MQ, OIDC, Outbox, and repository initialization; liveness must remain distinct.
- Shared CAS-backed idempotency for multi-instance production; Caffeine is an explicit single-instance/development fallback.
- Explicit CORS origin, credential, header, and method policy; no production `anyHost()` shortcut.
- Ownership and shutdown for JPA `EntityManagerFactory`, schedulers, listeners, and core runtime.
- Shutdown-hook registration/removal that does not accumulate during repeated starts or embedded tests.

## Gotchas

- A smoke test that returns 200 does not prove routing, auth, or DB behavior — each claim needs its own observable contract.
- Caffeine-backed idempotency is a single-instance fallback only; multi-instance production needs shared CAS, and the production profile should fail startup without it.
- `JavalinLifecycleParticipant` shutdown runs in reverse registration order; resources created first must close last, and rollback closes only what actually initialized.
- A shutdown hook registered per start accumulates across embedded tests and repeated starts — the repeated-start contract must assert no stale hooks remain.
- Readiness must aggregate real dependencies (DB, MQ, OIDC, Outbox); liveness must remain process-only — conflating them turns downstream outages into restart storms.
- CI start, artifact upload, or local build is not production acceptance; source, tests, reactor, containers, CI, publication, and consumption are separate gates that never imply one another.
- Javalin 6 and 7 APIs differ — `unsafe.routes` is relevant on Javalin 7, and shared behavior must be adapted per line, never copied mechanically.

## Output contract

At the start of non-trivial work, state: project type, detected SDD systems, fact source, current phase, execution method, next step, and whether files will change.

At handoff, state:

- active specification/plan and task status;
- changes per branch and exact local/tracking/remote SHAs;
- tests actually run, toolchain used, counts/results, and skipped gates;
- CI run/job conclusions, not merely run creation;
- publication coordinates and isolated empty-cache consumer evidence;
- unresolved compatibility, security, infrastructure, and production-acceptance risks.

Use explicit states such as `PASS`, `FAIL`, `BLOCKED`, `SKIPPED`, and `NOT RUN`. Never translate `BLOCKED` or `SKIPPED` into success.

## Common questions

1. **Can an existing plan be replaced?** No. Extend the active fact source unless the user authorizes migration or replacement.
2. **Can all lines use Maven 4?** No. Derive and preserve each line's current core/POM contract.
3. **Is a focused test enough?** It proves only that contract; run affected regression and the appropriate per-line gate.
4. **Does a push mean CI passed?** No. Resolve the run for the exact SHA and wait for terminal job conclusions.
5. **Does `deploy` upload activity mean release success?** No. Require a zero exit code, complete module inventory, remote metadata/integrity checks, and clean-cache consumption.
6. **What if Actions is blocked by billing?** Mark CI `BLOCKED`; do not change billing or secrets. Use local publication only when the user authorized it.

For failure patterns and edge cases, read [references/anti-patterns-and-faq.md](references/anti-patterns-and-faq.md).

## Deep Reference

- [Source Evidence Routing](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)
