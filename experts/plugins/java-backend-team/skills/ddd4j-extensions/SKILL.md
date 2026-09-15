---
name: ddd4j-extensions
description: Use when choosing, integrating, or reviewing optional ddd4j extensions such as Excel, license, monitoring, OpenTelemetry, PF4J, QLExpress, QR code, validation, or Jackson-related integration boundaries. 中文触发词：扩展集成、Excel 导出、License 校验、插件系统、规则表达式、二维码、可选依赖、降级。
license: Apache-2.0
---

# ddd4j Extensions

## Overview

Extensions are optional capabilities and must not pollute core in reverse. The current 3.0.x top-level extensions include Excel, License, Monitor, OTel, PF4J, QLExpress, QRCode, and Validation; Jackson core tooling lives in ddd4j-kit/core, and Akka currently lives mainly in ddd4j-boot.

## When to Use

- Deciding which extension covers a requirement: Excel export, license control, monitoring config, trace/metrics, plugin system, rule expressions, QR codes, or extended validation.
- Adding an extension as an optional dependency with a classpath guard so a missing jar never breaks core.
- Wiring the enabled switch, default implementation, user Bean override, and explicit close for an extension.
- Sandboxing risky inputs: QLExpress function/access/time limits, PF4J plugin signature/origin/isolation.
- Checking whether an extension actually exists on the current maintenance line before promising it.
- Reviewing degradation behavior when an extension is disabled or absent.

## When NOT to Use

Do not use this skill when:

- **Jackson / `JsonKit` / `EventPayloadSerializer` core tooling is the question** — use `ddd4j-kit` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-kit`.
- **OpenTelemetry metric design (names, labels, cardinality) is the question** — use `ddd4j-metrics` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-metrics`; this skill only covers the extension module's integration boundary.
- **Akka is the question** — it currently lives mainly in the ddd4j-boot extension, not a current core extension; use the boot-line skill instead.
- **A capability is claimed from a historical or Boot-only extension list** — do not use this skill to endorse it; verify against the current root POM first.
- **The request is to bypass license validation or run untrusted plugins unchecked** — do not use this skill for that; both are explicit refusals.
- **Generic PF4J / QLExpress / EasyExcel usage with no ddd4j extension involved** — use the generic `java-skills` or library-specific skills.

## Trigger Keywords

**English**: extension integration, optional dependency, classpath guard, plugin system, rule expression, license validation, graceful degradation, extension lifecycle

**中文**: 扩展集成, 可选依赖, 插件系统, 规则表达式, License 校验, 二维码, 优雅降级, 扩展生命周期

## Selection Matrix

| Requirement | Extension |
|---|---|
| Excel | extension-excel |
| License | extension-license |
| Logging/alerting configuration | extension-monitor |
| Trace/metrics | extension-otel |
| Plugin system | extension-pf4j |
| Rule expressions | extension-qlexpress |
| QR codes | extension-qrcode |
| Extended validation | extension-validation |

## Core Rules

1. A missing classpath entry must not affect core.
2. Extensions provide framework-agnostic capabilities; Boot/Quarkus and others handle assembly.
3. Configuration switches, default implementations, user overrides, and close are explicit.
4. Do not present historical/Boot-only extensions as current core modules.
5. Prove each item with the current module and its tests.

## Capability Boundaries

### ✅ Strong At

- Extension selection and integration.
- Core/extension/runtime boundaries.
- Optional dependencies and lifecycle.
- Extension testing and degradation.

### ⚠️ Needs Input

- Current maintenance line and target runtime.
- Target extension and configuration.
- External service/license requirements.

### ❌ Out of Scope

- Claiming support for a module that does not exist.
- Extension dependencies leaking into core.
- Bypassing license validation.

## Deep Reference

- [Current Extensions](references/current-extensions.md)
- [Integration Pattern](references/integration-pattern.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Workflow

### Step 1: Confirm the extension exists on the current line

Read the current root POM and directory listing — never a historical list — and identify the target extension (excel, license, monitor, otel, pf4j, qlexpress, qrcode, validation) plus any external dependency it needs (license server, plugin directory, OTel collector).

### Step 2: Wire conditionally

Add the dependency as optional, implement the classpath guard and the enabled switch in the runtime / Boot auto-configuration, and preserve user Bean overrides. A missing classpath entry must not affect core.

### Step 3: Sandbox risky inputs

Restrict QLExpress functions, accessed types, and timeouts via builder permissions; apply signature, origin, isolation, and permission policies to PF4J plugins. Never log license keys or secrets.

### Step 4: Define resource owners and close

Name the owner of every resource the extension creates (thread pools, plugin handles, collectors) and make close explicit and idempotent so shutdown does not leak.

### Step 5: Test real behavior and degradation

Run normal, disabled, classpath-missing, and shutdown paths. Disabling the extension must degrade cleanly — a configuration switch present is not evidence of behavior.

## Gotchas

- Historical extension lists presented as current — Akka lives mainly in ddd4j-boot and Jackson tooling lives in ddd4j-kit; only the root POM of the target line tells you what actually exists.
- Extension dependencies leaking into core as required entries — the integration compiles and tests pass, then the first deployment without the optional jar fails at boot.
- Treating the configuration switch as behavior — `extension.enabled=true` in Properties proves nothing until a real test exercises the extension's effect.
- QLExpress rules running without sandbox limits — an expression can call runtime methods or loop forever; function, access, and timeout restrictions are part of integration, not an optional extra.
- PF4J plugins trusted because they loaded — loading is not validation; signature, origin, isolation, and permission policies must be checked before a plugin runs.
- License keys or monitoring payloads reaching logs — these inputs are sensitive, and the extension's own debug logging is where they leak.

## Privacy and Security

License, monitoring, plugin, and expression inputs can be sensitive; never log secrets, and sandbox rules/plugins behind allowlists. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；License 密钥与插件内容仅以脱敏形式出现在示例中。

## Quick Start

- "Use `$ddd4j-extensions` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-extensions` to review existing usage against the current source."
- "Use `$ddd4j-extensions` to return an implementation choice, evidence state, and remaining risk."

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
