---
name: ddd4j-javalin-extensions
description: Use when composing optional ddd4j-javalin extensions, Guice modules, business overrides, SPI providers, and extension resource lifecycle. 中文触发词：Guice Module、业务覆盖、SPI Provider、扩展生命周期、模块组合。
license: Apache-2.0
---

# ddd4j-javalin Extensions

## Overview

Covers Guice Modules, Modules.override, business bindings, SPI providers, and extension lifecycle uniformly. Confirm the maintenance line with ddd4j-javalin-version-selection first, then read the current branch source.

## When to Use

- Composing optional ddd4j-javalin extensions with Guice Modules and `Modules.override` for business bindings on 6.7.x, 7.1.x, or 7.2.x.
- Registering SPI providers with unique implementations and verifying which provider wins for each contract.
- Assigning extension resources explicit lifecycle owners, idempotent close, and a defined failure policy (degrade versus fail startup).
- Testing the three composition paths: default wiring, business override, and disabled-on-classpath.

## When NOT to Use

Do not use this skill when:

- **Authoring a Quarkus extension is the question** — use `ddd4j-quarkus-extension-authoring` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-extension-authoring`.
- **The SPI contracts the extensions implement are being designed or changed** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Core runtime lifecycle participants (not extension-level ones) are the question** — use `ddd4j-javalin-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-runtime`.
- **A cross-capability review or release gate is needed** — use `ddd4j-javalin-production-hardening` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-production-hardening`.
- **Spring Boot auto-configuration composition is the question** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The project composes plain Guice modules without ddd4j** — do not use this skill; use `java-skills` instead, since the ddd4j extension contracts and lifecycle do not exist there.

## Trigger Keywords

**English**: Guice module, business override, SPI provider, extension lifecycle, composition, Modules.override

**中文**: Guice Module, 业务覆盖, SPI Provider, 扩展生命周期, 模块组合

## Core Scope

Guice Module, Modules.override, business bindings, SPI provider, extension lifecycle.

## Core Rules

1. 6.7.x, 7.1.x, and 7.2.x each keep their own Javalin/JDK/Maven/POM contract.
2. Javalin 6 versus 7 API differences are aligned by behavior, not copied mechanically.
3. Report configuration, startup, HTTP, containers, CI, and publishing in layers.
4. Context/Subject/resources are cleaned on success, exception, and async terminal states.
5. Production dependencies need real readiness, shared CAS, explicit CORS, and idempotent close.

## Capability Boundaries

### ✅ Strong At

- Implementation choice for extensions and Javalin adaptation.
- Lifecycle, configuration, and behavior boundaries.
- Differences across the three maintenance lines.

### ⚠️ Needs Input

- Target branch, POM, and Javalin version.
- Business behavior, dependencies, and deployment mode.
- Current source/test/CI evidence.

### ❌ Out of Scope

- Copying Javalin 6 code directly to 7.
- Substituting smoke tests for real behavior.
- Unauthorized releases or production changes.

## Workflow

### Step 1: Confirm the source of truth

Fix the maintenance line with `ddd4j-javalin-version-selection`, then locate the extensions module, the samples, and the module composition tests in the current checkout.

### Step 2: Compose the modules

Order the Guice Modules so defaults install first and business bindings override afterwards via `Modules.override`. Register SPI providers with unique implementations — one provider per contract.

### Step 3: Manage extension lifecycle

Give extension resources explicit owners and idempotent close, ordered against core resources by the reverse-registration shutdown rule. Confirm an optional extension's failure degrades without breaking the core runtime, while a required extension fails startup explicitly.

### Step 4: Test the composition paths

Run the composition tests: default wiring, business override taking effect, and the disabled-classpath path where the extension is absent. Exercise real behavior through the extension's public entry points, not just successful injector construction.

### Step 5: Report the composition

Produce a single report: module composition order and override points, SPI registrations and lifecycle owners, tests executed with evidence state per tier, and risks with proposed fixes and missing inputs.

## Gotchas

- `Modules.override` is order-sensitive — a business binding installed before the default module it overrides is silently ignored, and the service still starts with the default behavior.
- SPI providers must be unique per contract; duplicate implementations are a composition failure that surfaces as runtime nondeterminism, not as a startup error.
- Extension failure policy is per contract: optional extensions degrade, but an extension registered as required must fail startup explicitly — never both semantics on one registration.
- Extension resources need explicit owners and idempotent close; shutdown runs in reverse registration order, so extension cleanup is ordered against core resources, not independent of them.
- A class present on the classpath is not proof of composition — the disabled-classpath path must be executed as a test, or "optional" is untested guesswork.
- Javalin 6 and Javalin 7 APIs differ; extension code copied across maintenance lines must be re-verified on each line's toolchain.

## Output and Exceptions

When input is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Never output tokens, cookies, OIDC secrets, or database or private repository credentials.

本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；扩展示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-javalin-extensions` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-javalin-extensions` to review existing usage against the current source."
- "Use `$ddd4j-javalin-extensions` to return an implementation choice, evidence state, and remaining risk."

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
