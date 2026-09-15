---
name: ddd4j-annotation
description: Use when selecting, applying, reviewing, or extending current ddd4j annotations for DDD metadata, CQRS events, API behavior, ORM mapping, idempotency, auditing, or tenant fields. 中文触发词：注解选择、幂等注解、租户字段、审计字段、ORM 映射、事件注解、注解消费者。
license: Apache-2.0
---

# ddd4j Annotation

## Overview

Choose annotations by their consumers and runtime semantics. Do not assume that an annotation's name implies it registers a Bean, persists a field, or fires an event.

## When to Use

- Choosing which annotation family (ddd/Contract, cqrs, api, orm) fits a new field, method, or class.
- Applying `@BizKey`, `@TenantId`, `@SystemId`, `@OnCreate`, `@OnUpdate`, or `@OrderBy` to a PO and needing the consumer wired.
- Adding `@ApiIdempotent`, `ApiModule`, `ApiOperationLog`, or `RawResponse` to an endpoint and asking what must implement the behavior.
- Marking aggregate state changes with `CreateEvent`, `UpdateEvent`, or `DeleteEvent`.
- Reviewing existing annotation usage: retention, target, defaults, and whether a real consumer exists.
- Introducing a new ddd4j annotation and its test set (independence, default-value, target, consumer).

## When NOT to Use

Do not use this skill when:

- **The aggregate, command, or query model itself must be designed** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **The question is which module should own the annotation consumer, or dependency direction** — use `ddd4j-architecture` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-architecture`.
- **A Web or Runtime adapter must be implemented so the annotation actually does something** — use `ddd4j-web` or `ddd4j-runtime` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-web`.
- **Repository, interceptor, or persistence behavior behind ORM annotations must be built** — use `ddd4j-data` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-data`.
- **The annotations are Spring, Quarkus, or JPA annotations with no ddd4j involvement** — you should not map them onto ddd4j semantics here; use the generic `java-skills` or framework-specific skills.
- **The request is to claim a feature works because the annotation is present** — do not use this skill to certify behavior without a consumer test.

## Trigger Keywords

**English**: annotation selection, idempotency annotation, tenant field, audit fields, ORM mapping, event annotation, annotation consumer, retention target

**中文**: 注解选择, 幂等注解, 租户字段, 审计字段, ORM 映射, 事件注解, 注解消费者, 保留策略

## Quick Routing

| Need | Family |
|---|---|
| Domain classification and metadata | ddd, Contract, BusinessType |
| Create / Update / Delete events | cqrs |
| Idempotency, module, operation log, raw response | api |
| Domain / PO mapping, tenant, audit, ordering | orm |

## Usage Rules

1. Inspect Retention, Target, defaults, and consumers before applying.
2. `RUNTIME` retention only means the annotation is reflectively visible; it does not mean the framework auto-handles it.
3. ORM annotations are consumed by `DomainModelHelper`, repositories, or interceptors.
4. API annotations must have their behavior implemented by a Web / Runtime adapter.
5. New annotations must ship with independence, default-value, target, and consumer tests.
6. Verify package names and Java / Jakarta differences across maintenance lines.

## Capability Boundaries

### ✅ Strong At

- `Contract`, `BusinessType`, `DDDAnnotation`.
- `ApiIdempotent`, `ApiModule`, `ApiOperationLog`, `RawResponse`.
- `CreateEvent`, `UpdateEvent`, `DeleteEvent`.
- `DomainField`, `TenantId`, `SystemId`, `BizKey`, `OnCreate`, `OnUpdate`, `OrderBy`.

### ⚠️ Needs Input

- Current maintenance line.
- Annotation target element and intended consumer.
- Web, Data, or Runtime adapter availability.

### ❌ Out of Scope

- Claiming a feature works because an annotation is present.
- Treating Spring or Quarkus annotations as ddd4j annotations.
- Changing retention or target without compatibility review.

## Examples

```java
public final class OrderPO {
    @BizKey
    private String orderNo;

    @TenantId
    private String tenantId;

    @OnCreate
    private Instant createdAt;

    @OnUpdate
    private Instant updatedAt;
}
```

The example expresses metadata only. Whether the fields are populated and isolated depends on the Data adapter.

## Workflow

### Step 1: Define the contract

State the annotation's purpose, family (DDD / CQRS / API / ORM), target element, retention, and attribute defaults. Confirm the owning module and the Java / Jakarta package name for the target maintenance line.

### Step 2: Implement the annotation

Add the annotation class with explicit `@Retention`, `@Target`, and `@Documented`, and document every attribute default. Verify the exact package name against the current line's source before writing imports.

### Step 3: Wire the consumer

Implement or confirm the consumer in the Web, Data, or Runtime module — an interceptor, repository hook, registrar, or request-scope handler. An annotation without a consumer is inert metadata.

### Step 4: Test the chain

Run the reflective presence test, the default-value test, and the independence test (annotations coexisting on one element), then the consumer behavior test. Cross-build at least one other maintenance line.

### Step 5: Document and ship

Update the annotation's Deep Reference entry and capability-boundary list, and note privacy implications for tenant, audit, or log fields.

## Gotchas

- Treating `DDDAnnotation` as `@Component` — it is metadata only; nothing in the annotation itself registers a Bean, and `RUNTIME` retention only means it is reflectively visible.
- Shipping `@ApiIdempotent` without an `IdempotencyGuard` wired in — the endpoint compiles and returns 200 while allowing every duplicate request through.
- Letting the Domain reference PO classes after a `@DomainField` mapping is configured — the mapping goes one way; the domain must stay PO-free.
- A `@TenantId` field present but no tenant bound in the request context — the field silently stays null and rows land without tenant isolation.
- `@OnCreate` / `@OnUpdate` with no interceptor or repository hook backing them — the timestamps never populate, and reflection-only tests still pass.
- CQRS event annotations without a corresponding publish test — the event is declared but never fired.
- Copying annotation attributes from a higher maintenance line verbatim — Java / Jakarta package names and defaults differ per line.

## Output and Exceptions

Return `annotation FQN, retention, target, attributes, consumers, validation tests`. When a consumer is missing, return `missing: runtime handler; how to provide: confirm target Web/Data/Runtime module`.

## Deep Reference

- [DDD and Contract](references/ddd-and-contract.md)
- [API and CQRS](references/api-and-cqrs.md)
- [ORM](references/orm.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Log, tenant, and authentication-related annotations must not cause sensitive fields or full request bodies to leak. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；注解示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-annotation` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-annotation` to review existing usage against the current source."
- "Use `$ddd4j-annotation` to return an implementation choice, evidence state, and remaining risk."

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
