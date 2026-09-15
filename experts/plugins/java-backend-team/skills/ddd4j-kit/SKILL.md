---
name: ddd4j-kit
description: Use when selecting or applying current ddd4j utility APIs for JSON, bean mapping, strings, collections, identifiers, functions, dates, arrays, reflection, or low-level reusable helpers. 中文触发词：工具类、JSON 序列化、Bean 拷贝、字符串处理、集合工具、ID 生成、反射工具、Jackson。
license: Apache-2.0
---

# ddd4j Kit

## Overview

Prefer the stable utilities already shipped by ddd4j. Avoid duplicating them in business modules. Always confirm a tool's null handling, exception contract, type semantics, and thread safety before adopting it.

## When to Use

- Finding an existing utility before writing a private one: `StrKit`, `CollKit`, `ArrayKit`, `IdKit`, `DateKit`, `ReflectKit`.
- Choosing the right `JsonKit` mapper per scenario: `DEFAULT_OBJECT_MAPPER` for ordinary JSON, `REDIS_OBJECT_MAPPER` for trusted cache data, `EventPayloadSerializer` for events.
- Deciding between `BeanKit` and `MappingKit` for bean property handling, and where implicit copying is unsafe.
- Verifying a utility's null handling, exception contract, and generics before adopting it.
- Working with the Jackson 2 / 3 boundary, including the `com.fasterxml.jackson.annotation` compatibility package.
- Removing duplicate utility wrappers that Kit already provides.

## When NOT to Use

Do not use this skill when:

- **The domain/CQRS contracts the utilities support are the question** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Cache-side serialization policy (what may touch `REDIS_OBJECT_MAPPER`) is the question** — use `ddd4j-cache` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-cache`.
- **Domain-to-PO persistence mapping design is the question** — use `ddd4j-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-data`.
- **A request asks to treat a utility class as a domain service or to hide transactions/network/resource lifecycles behind Kit** — do not use this skill for that; Kit is stateless helper territory, and such requests get refused.
- **Generic Apache Commons / Guava / Hutool selection with no ddd4j involvement** — use the generic `java-skills`; this skill only adjudicates among ddd4j's own utilities.

## Trigger Keywords

**English**: utility class, JSON serialization, bean copy, string helpers, collection helpers, ID generation, reflection utility, Jackson mapper

**中文**: 工具类, JSON 序列化, Bean 拷贝, 字符串处理, 集合工具, ID 生成, 反射工具, Jackson 兼容

## Routing

| Need | Utility family |
|---|---|
| JSON / Jackson, type conversion | `JsonKit` |
| Bean properties and mapping | `BeanKit`, `MappingKit` |
| Strings | `StrKit`, `StrPool` |
| Collections and arrays | `CollKit`, `ArrayKit` |
| Identifiers | `IdKit` |
| Functions and type conversion | `FunctionKit` |
| Dates and times | `DateKit` and related formatters |
| Reflection | `ReflectKit` and explicit metadata tools |

## JSON Boundaries

- 3.0.x `JsonKit` uses `tools.jackson` databind.
- `DEFAULT_OBJECT_MAPPER` is for ordinary JSON.
- `REDIS_OBJECT_MAPPER` enables `DefaultTyping` and only handles trusted cache data.
- `EventStore` uses `EventPayloadSerializer` with explicit event types — never the Redis mapper.
- `com.fasterxml.jackson.annotation` exists as a Jackson 2 / 3 compatibility annotation package.

## Capability Boundaries

### ✅ Strong At

- Tool selection, null handling, and exception semantics.
- Boundary between `JsonKit` and Jackson 2 / 3.
- Common Bean, collection, string, and ID operations.
- Avoiding duplicate utility wrappers.

### ⚠️ Needs Input

- Current maintenance line.
- Input types and desired exception strategy.
- JSON usage scenario — HTTP, cache, or events.

### ❌ Out of Scope

- Treating utility classes as domain services.
- Enabling unrestricted polymorphism on untrusted JSON.
- Using Kit to hide transactions, network, or resource lifecycles.

## Workflow

### Step 1: Search the current Kit first

Before writing any helper, search the maintenance line's Kit sources for an existing method. Business modules duplicating `StrKit` / `CollKit` logic is the default failure this skill prevents.

### Step 2: Read the signature, implementation, and tests

Do not infer semantics from the method name. Read what null inputs do, which exceptions are thrown, and what the existing tests actually assert.

### Step 3: Classify the utility

Distinguish pure functions, global mutable mappers (`DEFAULT_OBJECT_MAPPER` vs `REDIS_OBJECT_MAPPER`), and side-effecting utilities. The class determines what the call site may assume about state and thread safety.

### Step 4: Pick the narrowest API

Choose the method that preserves `Optional`, exceptions, and generics rather than the one that silently coerces. The narrowest correct API beats the most convenient lossy one.

### Step 5: Test boundary values and error paths

Exercise null, empty, oversized, and malformed inputs plus the error path itself — utility semantics at the boundaries are exactly where "worked in my test" diverges from production behavior.

## Gotchas

- The `JacksonKit` name was merged away — code and AI-generated snippets referencing it do not compile on 3.0.x, which is the tell that the snippet came from an older line.
- 3.0.x `JsonKit` binds to `tools.jackson`, while older lines and most Stack Overflow answers use `com.fasterxml.jackson` — imports that look right fail to resolve.
- `REDIS_OBJECT_MAPPER` enables `DefaultTyping` — deserializing any external payload through it invites polymorphic deserialization attacks; it is for trusted cache data only.
- `BeanKit` copies properties silently — a renamed field or type mismatch becomes a null/zero target value with no error, which is why explicit Domain-to-PO mapping exists.
- Utility exceptions swallowed into `null` or `false` returns convert failures into fake successes downstream; preserve diagnosable exceptions at the call site.
- `EventStore` payloads go through `EventPayloadSerializer` with explicit event types — pointing them at the Redis mapper compiles and corrupts the event log.
- 3.0.x utility signatures are not backward-portable — a method present on the high line may not exist (or may differ) on 1.0.x/2.0.x; verify per line.

## Output and Exceptions

Return the utility FQN, maintenance line, inputs and outputs, and null / exception semantics. When missing, return `missing: target type or maintenance line; how to provide: call site and POM`.

## Deep Reference

- [JSON and Jackson](references/json-and-jackson.md)
- [Bean, String, and Collection](references/bean-string-collection.md)
- [ID, Function, and Reflection](references/id-function-reflection.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

JSON, logs, and exceptions must not expose tokens, passwords, private fields, or private-repository credentials. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；工具类示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-kit` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-kit` to review existing usage against the current source."
- "Use `$ddd4j-kit` to return an implementation choice, evidence state, and remaining risk."

## Audience and Customization

- Developers: provide the target maintenance line, POM, capabilities, and acceptance behavior.
- Architects: specify a read-only boundary, compatibility, or migration review.
- Testers / release engineers: specify the required evidence levels; do not auto-expand to release or production operations.

Customize the target framework, allowed implementations, excluded modules, compatibility requirements, and evidence level. When input is insufficient, give a tentative verdict first, then list `missing: specific item; how to provide: path or configuration`.

## FAQ

1. **Are skills organized by Maven artifact?** No — by the user-facing capability domain.
2. **Can I copy another maintenance line directly?** No — verify the version and source first.
3. **Does a class existing in source prove the capability works?** No — registration and behavior evidence are also required.
4. **How do I report tests that did not run?** Mark `NOT RUN` or `BLOCKED`.
5. **Can the skill commit or release automatically?** Only after explicit user authorization.
6. **What if the implementation is missing?** Describe the missing module or evidence; do not invent APIs.
