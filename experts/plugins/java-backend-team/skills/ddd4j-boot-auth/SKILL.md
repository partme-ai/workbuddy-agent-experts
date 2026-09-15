---
name: ddd4j-boot-auth
description: Use when choosing or integrating Sa-Token, Apache Shiro, or Spring Security through ddd4j-boot auto-configuration, Subject mapping, exception handling, and request lifecycle. 中文触发词：认证集成、Sa-Token、Shiro、Spring Security、Subject 映射、登录鉴权、异常映射、请求清理。
license: Apache-2.0
---

# ddd4j-boot Auth

## Overview

Covers Sa-Token, Shiro, Spring Security, SubjectProvider, exceptions, and request cleanup uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Choosing among Sa-Token, Apache Shiro, and Spring Security for a ddd4j-boot service and assembling it through the boot auth auto-configuration.
- Wiring a `SubjectProvider` so the ddd4j `Subject` contract is populated from the chosen security framework.
- Mapping authentication exceptions (expired token, insufficient role) onto the web error contract.
- Auditing request cleanup — that tokens and Subject state do not leak across pooled request threads.
- Configuring or overriding the auth defaults (user beans versus `@ConditionalOnMissingBean` defaults) on a specific Boot line (2.3–4.1).
- Verifying the full auth behavior matrix: anonymous, valid, expired, insufficient-role, logout, and thread reuse.

## When NOT to Use

Do not use this skill when:

- **The `Subject` contract or identity model itself needs changing** — use `ddd4j-auth` (framework-agnostic auth) or `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-auth`.
- **The error-response format the exceptions map to is the question** — use `ddd4j-boot-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-web`.
- **Generic auto-configuration mechanics (registration files, off switches, destroy methods) are the question, not auth** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The runtime is Javalin, Quarkus, or Spring Cloud** — use the matching `ddd4j-javalin-auth`, `ddd4j-quarkus-auth`, or `ddd4j-cloud-*` skill instead; the Boot assembly should not be transplanted.
- **The project is plain Spring Boot without ddd4j** — generic Spring Security / Sa-Token skills apply; the `SubjectProvider` assembly does not exist there.
- **Token payloads or user credentials need inspecting** — do not output real tokens or secrets; troubleshooting output must redact sensitive values.

## Trigger Keywords

**English**: authentication integration, Sa-Token, Shiro, Spring Security, Subject mapping, login and roles, exception mapping, request cleanup

**中文**: 认证集成, Sa-Token, Shiro, Spring Security, Subject 映射, 登录鉴权, 异常映射, 请求清理
## Core Scope

Sa-Token, Shiro, Spring Security, SubjectProvider, exceptions, and request cleanup.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among authentication implementations and Spring Boot assembly.
- Configuration, overrides, lifecycle, and verification.
- Maintenance-line compatibility judgments.

### ⚠️ Needs Input

- Target Boot line, POM, and configuration.
- Business behavior, dependencies, and deployment mode.
- Current test/CI/runtime evidence.

### ❌ Out of Scope

- Modifying ddd4j core public semantics.
- Substituting dependency or bean presence for real behavior.
- Unauthorized releases or production operations.

## Workflow

### Step 1: Confirm the source of truth

Run `ddd4j-boot-version-selection` to fix the line, then locate the auth AutoConfiguration, its Properties, and the corresponding `ddd4j-auth` modules on that line.

### Step 2: Select the security framework

Compare Sa-Token, Shiro, and Spring Security against the account model and the team's existing investment. Confirm exactly one primary `SubjectProvider` ends up assembled — two active providers is a defect, not a fallback.

### Step 3: Verify the wiring

Check the conditional wiring, default beans, and user bean override points. Confirm the off switch truly skips assembly, and that exception handling maps every auth failure onto the web error contract.

### Step 4: Test the behavior matrix

Execute context and behavior tests covering: anonymous access, valid credentials, expired token, insufficient role, logout, and thread reuse after a request. Assert that no Subject or token leaks across requests.

### Step 5: Report with separated evidence

Report the selected framework and artifacts with configuration keys, the AutoConfiguration entry and override points, test results, and evidence state — configuration presence, bean creation, behavior, CI, and publish reported separately — plus risks and missing inputs.

## Gotchas

- Multiple auth starters on the classpath can each assemble a `SubjectProvider`; "it works" may mean the wrong one won. Exactly one primary provider must be proven, not assumed.
- A user-declared `SubjectProvider` bean silently replaces the assembled default via `@ConditionalOnMissingBean` — swapping implementations changes exception semantics that were never re-tested.
- Auth filters bind Subject state per request; a missing cleanup on the exception path leaves one user's identity bound to a pooled thread for the next request.
- Bean creation is not authentication working: a context that starts proves wiring, not that an expired token is rejected.
- Sa-Token, Shiro, and Spring Security map the same failure (expired session) to different exception types — the mapping to the web error contract must be verified per chosen framework, not once for the skill.
- Copying the auth wiring from a Boot 2 line to a Boot 3+ line breaks on the registration file and API changes; each line adapts individually.
- Printing the auth configuration for troubleshooting can leak secrets or tokens — sensitive values must be redacted.

## Output and Exceptions

When information is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output credentials, tokens, production connection strings, or sensitive business data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；令牌与身份信息仅以脱敏形式出现。

## Quick Start

- "Use `$ddd4j-boot-auth` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-auth` to review existing usage against the current source."
- "Use `$ddd4j-boot-auth` to return an implementation choice, evidence state, and remaining risk."

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
