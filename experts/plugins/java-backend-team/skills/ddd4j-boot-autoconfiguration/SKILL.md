---
name: ddd4j-boot-autoconfiguration
description: Use when creating or reviewing ddd4j Spring Boot auto-configurations, configuration properties, conditional beans, imports metadata, user overrides, and bean lifecycle. 中文触发词：自动配置、条件装配、配置属性、用户覆盖、imports 注册、Bean 生命周期、开关。
license: Apache-2.0
---

# ddd4j-boot Auto-Configuration

## Overview

Covers AutoConfiguration, ConfigurationProperties, ConditionalOnClass/Property/MissingBean, imports, and destroyMethod uniformly, not split per artifact. Before use, confirm the maintenance line through ddd4j-boot-version-selection.

## When to Use

- Writing or reviewing a `*AutoConfiguration` class for a ddd4j-boot feature module, including its conditions and configuration prefix.
- Deciding where user overrides apply: which defaults carry `@ConditionalOnMissingBean` and which properties back off.
- Wiring an "off switch" — a property that must skip the whole assembly, not just one bean.
- Checking registration metadata: Boot 2.x `spring.factories` versus Boot 3.x+ `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`.
- Auditing resource lifecycle: `destroyMethod`, resource ownership, failure rollback, and idempotent close.
- Diagnosing why a configuration class on the classpath produces no beans, or produces the wrong default.

## When NOT to Use

Do not use this skill when:

- **The question is module layout or which POM owns what** — use `ddd4j-boot-architecture` or `ddd4j-boot-bom` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-architecture`.
- **The domain contracts being wired (aggregates, commands, repositories) need changing** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **A specific feature's behavior is the question (data source, cache, MQ, web, auth)** — use the matching `ddd4j-boot-data`, `ddd4j-boot-cache`, `ddd4j-boot-mq`, `ddd4j-boot-web`, or `ddd4j-boot-auth` skill instead; do not use this generic wiring skill to design feature semantics.
- **The runtime is Quarkus (build-time wiring) or Javalin (manual wiring)** — use the matching `ddd4j-quarkus-*` or `ddd4j-javalin-*` skill instead; Spring Boot auto-configuration mechanics should not be transplanted to them.
- **The project is plain Spring Boot without ddd4j** — generic Spring Boot starter/auto-configuration skills apply.
- **A bean exists but the external service is unreachable** — this skill should not substitute bean creation for real connectivity or behavior evidence.

## Trigger Keywords

**English**: auto-configuration, conditional wiring, configuration properties, user overrides, imports registration, bean lifecycle, off switch

**中文**: 自动配置, 条件装配, 配置属性, 用户覆盖, imports 注册, Bean 生命周期, 开关
## Core Scope

AutoConfiguration, ConfigurationProperties, ConditionalOnClass/Property/MissingBean, imports, destroyMethod.

## Core Rules

1. Gather evidence from the current target line's POMs, source, and tests.
2. Default implementations allow explicit user overrides; an off switch must truly skip assembly.
3. Report configuration presence, bean creation, behavior tests, CI, and publishing separately.
4. Resources must have an explicit owner, failure rollback, and idempotent close.
5. Handle Boot 2/3/4 API, JDK, and Maven differences line by line.

## Capability Boundaries

### ✅ Strong At

- Choosing among auto-configuration implementations and Spring Boot assembly.
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

Run `ddd4j-boot-version-selection` to fix the line, then locate the feature's AutoConfiguration class, its Properties, and the imports metadata for that line's registration mechanism.

### Step 2: Map conditions and defaults

List the `@ConditionalOnClass` / `@ConditionalOnProperty` / `@ConditionalOnMissingBean` conditions and the configuration prefix. Identify which beans are defaults and where a user bean or property legitimately overrides them.

### Step 3: Verify the wiring semantics

Confirm the off switch truly skips assembly — a disabled feature must not register leftover beans. Confirm `destroyMethod`, resource ownership, failure rollback, and idempotent close for every resource the configuration creates.

### Step 4: Test the paths

Execute the target module's context tests and behavior tests. Cover the user-override path explicitly: with a user bean present, the default must back off, and with the feature disabled, nothing assembles.

### Step 5: Report with separated evidence

Report the version line, configuration entry points, defaults and override points, test results, and risks. Keep configuration presence, bean creation, behavior tests, CI, and publishing as separate evidence layers.

## Gotchas

- Boot 2.x registers auto-configuration via `spring.factories`; Boot 3.x+ uses `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`. Checking the wrong file for the line shows an empty configuration and sends you hunting a bug that does not exist.
- A configuration class existing on the classpath does not mean it is registered, and registration does not mean conditions passed — three separate gates, each failing differently.
- `@ConditionalOnMissingBean` means a user-declared bean silently replaces the default; an "off switch" property must actually skip assembly, not merely skip one bean and leave its collaborators half-wired.
- A `destroyMethod` that never runs leaks connections and thread pools on context close — the leak appears only at shutdown or in long test suites, never in the happy path.
- Bean creation is not external-service availability: a context that starts proves wiring, not connectivity.
- Copying an auto-configuration from a newer line to an older one fails on Boot/JDK API differences; each line adapts the registration and API individually.
- Printing configuration for troubleshooting can leak credentials — sensitive property values must be redacted before output.

## Output and Exceptions

When information is missing, output "missing: target line/implementation/configuration; how to provide: supply the POM and acceptance behavior", and continue safe read-only checks.

## Deep Reference

- [Feature Matrix](references/feature-matrix.md)
- [Source Evidence](references/source-evidence.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security


Never output credentials, tokens, production connection strings, or sensitive business data. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；配置输出必须先脱敏。

## Quick Start

- "Use `$ddd4j-boot-autoconfiguration` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-boot-autoconfiguration` to review existing usage against the current source."
- "Use `$ddd4j-boot-autoconfiguration` to return an implementation choice, evidence state, and remaining risk."

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
