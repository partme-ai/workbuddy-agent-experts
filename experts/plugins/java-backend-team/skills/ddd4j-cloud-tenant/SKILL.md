---
name: ddd4j-cloud-tenant
description: Use when implementing or reviewing ddd4j-cloud tenant and system isolation, Tenant annotations, context holders, data scope, ignore rules, SQL filtering, or cross-service propagation. 中文触发词：租户隔离、数据权限、数据范围、SQL 过滤、跨服务传播、忽略规则、系统上下文。
license: Apache-2.0
---

# ddd4j-cloud Tenant

## Overview

Covers the Tenant annotation, TenantContextHolder, system isolation, data scope, SQL, and cross-service propagation uniformly, not split per artifact. Choose the Cloud→Boot→ddd4j primary combination first, then read the current branch.

## When to Use

- Wiring the Tenant annotation and `TenantContextHolder` at request entry in a ddd4j-cloud service.
- Applying data scope and tenant SQL filtering, and deciding which tables are exempt.
- Writing or auditing tenant ignore rules for system and background operations.
- Propagating the tenant id across async, Reactor, Feign, and cross-service calls.
- Defining system-context semantics for background and cross-service work.
- Diagnosing cross-tenant data leaks or reads returning another tenant's rows.

## When NOT to Use

Do not use this skill when:

- **Non-tenant request context is the question** (Subject, trace, general headers) — use `ddd4j-cloud-context` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-context`.
- **The `Contexts`/`Subject`/`ThreadContext` SPI contracts themselves are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Feign interceptor plumbing is the question** — use `ddd4j-cloud-feign` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-feign` (tenant headers ride along, but the wiring belongs there).
- **The datasource, MyBatis/JPA stack, or transaction strategy is the question** — use `ddd4j-cloud-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cloud-data`.
- **The wiring is plain Spring Boot ddd4j with no Cloud modules** — use `ddd4j-boot-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-data`.
- **Generic multi-tenant SaaS design without ddd4j** — do not use this skill; apply generic architecture guidance instead (no install command).

## Trigger Keywords

**English**: tenant isolation, data scope, SQL filtering, cross-service propagation, tenant ignore rules, system context, tenant holder

**中文**: 租户隔离, 数据权限, 数据范围, SQL 过滤, 跨服务传播, 忽略规则

## Core Scope

Tenant annotation, TenantContextHolder, system isolation, data scope, SQL, cross-service propagation.

## Core Rules

1. Primary combinations and compatible alternatives are kept separate; never guess Boot/ddd4j from the branch name.
2. Old cmpt and new extensions naming must not be mixed.
3. Context/Tenant are restored on sync, async, Reactor, and Feign terminal states.
4. Binder, database, Nacos, Sentinel, and the like need real external behavior evidence.
5. Upstream gaps, Cloud failures, CI, publishing, and consumption are classified separately.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for tenancy and Spring Cloud integration.
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

Run `ddd4j-cloud-version-selection` to fix the combination, then locate the data tenant, MyBatis, and Feign tenant modules on the confirmed branch and SHA.

### Step 2: Map the isolation surface

Identify where the tenant id enters (request header, token), how it reaches `TenantContextHolder`, where the ignore rules live, and where SQL filtering applies — including which tables are exempt.

### Step 3: Verify propagation

Confirm tenant propagation across sync, async, Reactor, and Feign calls, and confirm system-context semantics for background and cross-service operations.

### Step 4: Test isolation

Run isolation tests: cross-tenant reads blocked, data scope enforced, ignore rules respected — covering exception, async, and Feign round-trips against a real store.

### Step 5: Report the isolation map

Output the isolation map (entry → holder → filter → propagation) with file paths, the ignore-rule inventory with justification, tests executed with evidence state per tier, and violations with proposed fixes.

## Gotchas

- A tenant ignore rule intended for system operations will silently leak cross-tenant reads if the ignore condition is too broad — audit every rule against the exact operations it was created for.
- `TenantContextHolder` is thread-bound like any `ThreadLocal`: async, Reactor, and Feign hops drop the tenant unless explicitly propagated, and a background job that sets system context and never clears it poisons the pooled thread for normal requests.
- SQL filtering applies at the data layer — any access path that bypasses the repository (native clients, ad-hoc queries) silently skips the filter.
- The exempt-table list drifts from schema migrations: a newly added business table starts unfiltered unless someone updates the exemption inventory deliberately.
- A tenant id taken from a request header must be validated against the Subject/token — trusting the header alone lets any client read another tenant by forging it.
- Tenant tests with a mocked holder prove wiring shape only; cross-tenant blocking must be proven against a real database, including the exception and Feign paths.

## Output and Exceptions

When input is missing, output "missing: Cloud line/upstream/external services; how to provide: supply the POM and acceptance behavior".

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output Nacos/Redis/broker/database/private repository credentials or real tenant data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例中的租户标识均为虚构，不涉及任何真实租户数据。

## Quick Start

- "Use `$ddd4j-cloud-tenant` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cloud-tenant` to review existing usage against the current source."
- "Use `$ddd4j-cloud-tenant` to return an implementation choice, evidence state, and remaining risk."

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
