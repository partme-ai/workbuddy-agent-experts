---
name: ddd4j-auth
description: Use when choosing, integrating, or reviewing ddd4j authentication and authorization with Sa-Token, Apache Shiro, or Spring Security, including Subject mapping, roles, permissions, sessions, temporary tokens, and exception handling. 中文触发词：认证授权、Sa-Token、Shiro、Spring Security、Subject 映射、角色权限、临时令牌、会话清理。
license: Apache-2.0
---

# ddd4j Auth

## Overview

All three frameworks map onto the ddd4j Subject/AuthPrincipal/SubjectProvider; domain and application code never binds directly to a concrete security context.

## When to Use

- Choosing between Sa-Token, Apache Shiro, and Spring Security for a ddd4j project.
- Implementing a `SubjectProvider` that maps the framework's identity onto `AuthPrincipal` (profile, roles, permissions).
- Wiring temporary tokens (`SaTempToken`), API keys, or multiple account types via `StpKit.DEFAULT/ADMIN/USER`.
- Binding the Subject into the request context at entry and cleaning it up at request end.
- Converting framework exceptions (login expired, insufficient permission) into stable web errors.
- Reviewing anonymous, expired, insufficient-role, thread-reuse, and logout test coverage.

## When NOT to Use

Do not use this skill when:

- **The HTTP-level error contract is the question** (status codes, unified payload shape for 401/403) — use `ddd4j-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-web`.
- **The request-scope binding mechanics in the runtime are the question** — use `ddd4j-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-runtime`.
- **Token or session storage in Redis is the question** — use `ddd4j-cache` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cache`.
- **Framework configuration unrelated to the ddd4j Subject mapping** (e.g. a standalone Spring Security OAuth2 server) — use the framework's own skills; mapping it to ddd4j is the only part this skill covers.
- **The request is to bypass authentication, read another user's session, or forge a Subject** — do not use this skill for that; it is an explicit out-of-scope refusal.
- **Version or artifact selection is the question** — use `ddd4j-version-selection` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-version-selection`.

## Trigger Keywords

**English**: Sa-Token, Shiro, Spring Security, Subject mapping, roles and permissions, temporary token, session cleanup, login flow

**中文**: 认证授权, Subject 映射, 角色权限, 临时令牌, 会话清理, 登录流程, 令牌过期, 线程复用

## Framework Selection

| Scenario | Recommendation |
|---|---|
| Multiple account types, temporary tokens, lightweight domestic projects | Sa-Token |
| Existing Realm/Subject/Permission | Shiro |
| Spring enterprise security, OAuth2/OIDC, method security | Spring Security |

## Unified Chain

Authentication framework → SubjectProvider → ddd4j Subject → AuthPrincipal → request Context → application/domain services.

Each implementation must state its dependencies, configuration, identity mapping, roles and permissions, exceptions, context cleanup, and tests.

## Capability Boundaries

### ✅ Strong At

- The Subject/AuthPrincipal/Provider abstraction.
- Selecting and using Sa-Token, Shiro, and Spring Security.
- Temporary tokens, API keys, roles and permissions.
- Request lifecycle and exception mapping.

### ⚠️ Needs Input

- Current maintenance line, runtime, and authentication framework.
- Token/Session mode and account model.
- Roles, permissions, tenants, and logout requirements.

### ❌ Out of Scope

- Bypassing authentication or operating another user's account.
- Treating Same-Token as an end-user token.
- Reading SecurityContext/StpUtil/Shiro SecurityUtils in the domain layer.

## Workflow

### Step 1: Select the framework and confirm the artifacts

Pick Sa-Token, Shiro, or Spring Security against the account model (multiple account types, temporary tokens, OAuth2/OIDC, method security), then confirm the actual artifacts on the classpath — the choice only counts if the dependency and version are real.

### Step 2: Define the AuthPrincipal

Model the profile, roles, and permissions as `AuthPrincipal`. This is the only identity shape the domain and application layers will ever see.

### Step 3: Implement and assemble the SubjectProvider

Implement exactly one primary `SubjectProvider` that translates the framework's identity into the ddd4j `Subject`. Registering more than one framework's provider invites contention over the same contract.

### Step 4: Bind at request start; restore and clean up at request end

Bind the Subject into the request/thread context at the entry point, and restore the previous value in a scope or `finally` so cleanup covers success, exception, and async completion.

### Step 5: Convert framework exceptions into stable web errors

Map login-required, token-expired, and insufficient-permission exceptions to the stable error contract instead of letting framework-specific types leak outward.

### Step 6: Test all paths

Cover anonymous access, valid login, expired token, insufficient role, thread reuse after logout, and the request-end cleanup itself — not just the happy login.

## Gotchas

- Assembling Sa-Token, Shiro, and Spring Security at once — two `SubjectProvider`s then contend for the same contract, and whichever registers last silently wins.
- Hardcoding Sa-Token extra keys as string literals — extended fields must go through `AuthConstants` and the type-safe getters, or renamed keys break at runtime.
- Leaving `SecurityContext` / Shiro `Subject` bound after the request — on a pooled thread, the next request inherits the previous user's identity, and only exception-path testing reveals it.
- Testing only successful login — the request-end cleanup, logout, and expired-token paths are where leaks and 500-instead-of-401 bugs actually live.
- Logging full tokens or API keys — keep redacted fingerprints only; logs outlive sessions.
- Treating a BOM dependency as proof that authentication is enabled — the artifact on the classpath says nothing about a registered `SubjectProvider`.
- Treating Sa-Token's Same-Token as an end-user token — it is an inner-call/gateway token with different semantics and must not authenticate users.

## Output and Exceptions

Output the framework choice, artifacts, configuration, Subject mapping, lifecycle, and tests. When input is missing, write "missing: authentication framework/mode/runtime; how to provide: supply the POM and redacted configuration".

## Deep Reference

- [Framework Selection](references/framework-selection.md)
- [Sa-Token](references/satoken.md)
- [Shiro](references/shiro.md)
- [Spring Security](references/spring-security.md)
- [Subject Lifecycle](references/subject-lifecycle.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Use fictional identities only; tokens, API keys, sessions, and organization/role data must be redacted. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；身份、令牌与会话示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-auth` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-auth` to review existing usage against the current source."
- "Use `$ddd4j-auth` to return an implementation choice, evidence state, and remaining risk."

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
