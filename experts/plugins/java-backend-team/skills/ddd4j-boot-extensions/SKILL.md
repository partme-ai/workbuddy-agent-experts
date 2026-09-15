---
name: ddd4j-boot-extensions
description: Use when integrating optional ddd4j-boot extensions such as Akka, Excel, QLExpress, QR code, monitoring, and other conditionally configured Spring Boot capabilities. 中文触发词：扩展集成、Akka、Excel、QLExpress、QR Code、Monitor、条件装配、可选模块。
license: Apache-2.0
---

# ddd4j-boot Extensions

## Overview

Covers Akka, Excel, QLExpress, QRCode, Monitor, and other current extensions uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Deciding whether a need (Akka actors, Excel export, QLExpress rules, QR code generation, monitoring helper) maps to an existing `ddd4j-boot-extensions` submodule.
- Wiring an optional extension through its auto-configuration: classpath guards, enabled switches, and `@ConditionalOnMissingBean` defaults.
- Verifying that disabling an extension degrades gracefully without breaking core assembly.
- Checking that an extension is guarded on the classpath so absence of its third-party library skips assembly instead of failing startup.
- Adding usage evidence for an extension: enabled, disabled, and classpath-missing context tests.
- Marking requested-but-absent extensions as NOT IMPLEMENTED instead of inventing modules or APIs.

## When NOT to Use

Do not use this skill when:

- **The extension logic itself (utility code, not wiring) is the question** — use `ddd4j-kit` or `ddd4j-extensions` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-extensions`.
- **Generic auto-configuration mechanics are the question, not a specific extension** — use `ddd4j-boot-autoconfiguration` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration`.
- **The capability has a dedicated Boot skill (data, cache, MQ, web, auth, observability)** — use that skill instead; extensions are the optional remainder, not a catch-all.
- **The runtime is Javalin or Quarkus** — use the matching `ddd4j-javalin-extensions` or `ddd4j-quarkus-extension-authoring` skill instead; the Boot extension modules do not transfer.
- **The request is for a capability that does not exist in the current line's submodules** — do not use this skill to design a new one from scratch; mark NOT IMPLEMENTED and route to the architecture skill.
- **The project is plain Spring Boot without ddd4j** — integrate the third-party libraries directly with generic Spring Boot skills; the extension modules should not be transplanted.

## Trigger Keywords

**English**: extensions integration, Akka, Excel, QLExpress, QR code, Monitor, conditional wiring, optional module

**中文**: 扩展集成, Akka, Excel, QLExpress, QR Code, Monitor, 条件装配, 可选模块
## Core Scope

Akka, Excel, QLExpress, QRCode, Monitor, and other current extensions.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among extension implementations and Spring Boot assembly.
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

Run `ddd4j-boot-version-selection` to fix the line, then list the current `ddd4j-boot-extensions` submodules from the root POM — the set differs across the Boot 2.3–4.1 lines.

### Step 2: Select the extension

Match the need (Akka, Excel, QLExpress, QRCode, Monitor, and others) to an existing submodule on that line. Mark anything absent as NOT IMPLEMENTED rather than inventing a module or API.

### Step 3: Verify the wiring

Check the classpath guards, the enabled switch, conditional wiring, and user bean override points. Confirm every resource the extension creates has an owner, failure rollback, and idempotent close.

### Step 4: Test all three states

Execute context tests and real behavior tests for the three decisive states: enabled, disabled, and classpath-missing. Confirm that disabling degrades gracefully without breaking core assembly.

### Step 5: Report with separated evidence

Report the chosen extensions with configuration keys, the AutoConfiguration entry and override points, test results, and evidence state — configuration presence, bean creation, behavior, CI, and publish reported separately — plus risks and missing inputs.

## Gotchas

- An extension submodule existing in the root POM does not mean it is assembled at runtime — classpath guards and enabled switches decide independently, and each can silently veto.
- Optional extensions can hard-depend on their third-party library; a classpath guard that checks the wrong class produces `ClassNotFoundException` at startup instead of a graceful skip.
- Disabling an extension is only real if the whole assembly backs off — a leftover health indicator or filter from the extension keeps running after the "off" switch.
- QLExpress-style script extensions execute user-supplied expressions; the assembly is not the place to loosen security, and printed configuration can leak scripts or credentials.
- The extension set differs per maintenance line — a submodule present on 3.x may not exist on 2.x, and copying config across lines references a module that does not exist.
- Extension features requested but absent from the current line must be marked NOT IMPLEMENTED; inventing a plausible-sounding module is the failure this skill exists to prevent.

## Output and Exceptions

When information is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output credentials, tokens, production connection strings, or sensitive business data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-boot-extensions` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-extensions` to review existing usage against the current source."
- "Use `$ddd4j-boot-extensions` to return an implementation choice, evidence state, and remaining risk."

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
