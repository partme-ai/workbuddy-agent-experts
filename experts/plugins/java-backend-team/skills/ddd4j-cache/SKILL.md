---
name: ddd4j-cache
description: Use when choosing, configuring, implementing, or reviewing ddd4j cache providers, local caches, Redis clients, JetCache, Memcached, TTL, locking, CAS, statistics, or cache-backed idempotency. 中文触发词：本地缓存、Redis、Redisson、JetCache、TTL、分布式锁、CAS 幂等、缓存键。
license: Apache-2.0
---

# ddd4j Cache

## Overview

Choose single-node or distributed consistency semantics first, then choose the implementation. All implementations are consumed by upper layers through the core Cache/CacheManager/CasCache/AtomicCache contracts.

## When to Use

- Choosing between Caffeine/Guava/Hutool (single-JVM), Lettuce/Jedis (native Redis), Redisson (distributed locks/objects), JetCache (multilevel), or Memcached.
- Implementing cluster-safe idempotency on the `AtomicCache` / `CasCache` / `GetsResponse` contracts.
- Configuring and testing TTL semantics — units, zero/negative values, and precision per implementation.
- Designing cache keys with tenant isolation and without PII.
- Reviewing lock ownership, timeouts, and release-on-exception behavior.
- Deciding what happens when Redis is unavailable — degradation vs silent success.

## When NOT to Use

Do not use this skill when:

- **The idempotency contract at the HTTP/API layer is the question** — use `ddd4j-web` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-web`.
- **Redis Stream used as a message broker is the question** — use `ddd4j-mq` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-mq`.
- **The core `Cache` SPI contract itself needs to be designed or changed** — use `ddd4j-core` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core`.
- **Session/token storage strategy is the question** — use `ddd4j-auth` instead. Install: `npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-auth`.
- **Generic Redis/Redisson tuning with no ddd4j contract involved** — use the generic `java-skills` or Redis-specific skills; do not map ddd4j SPI names onto an unrelated setup.
- **The request treats the cache as the system of record** — do not use this skill to legitimize that; data authority belongs to the source of truth, not the cache.

## Trigger Keywords

**English**: local cache, Redis client, distributed lock, TTL semantics, CAS idempotency, cache key, JetCache, degradation

**中文**: 本地缓存, Redis 客户端, 分布式锁, TTL 语义, CAS 幂等, 缓存键, JetCache, 缓存降级

## Implementation Selection

| Scenario | Implementation |
|---|---|
| Single-JVM high performance | Caffeine, Guava, Hutool |
| Native Redis clients | Lettuce, Jedis |
| Distributed locks/objects | Redisson |
| Multilevel/unified abstraction | JetCache |
| Memcached | MemcachedCache |

## Core Rules

1. Caffeine/Guava/Hutool provide no cross-instance consistency.
2. Cluster idempotency requires a shared atomic compare-and-set, not just distributed storage.
3. TTL units, zero values, negative values, and precision must be tested per implementation.
4. REDIS_OBJECT_MAPPER handles trusted cache data only.
5. Locks must have an owner, a timeout, and release on exception.
6. CacheStats cannot substitute for business success metrics.

## Capability Boundaries

### ✅ Strong At

- Implementation selection and configuration.
- TTL, locks, CAS, statistics.
- Local versus distributed semantics.
- Reviewing cache-backed idempotency.

### ⚠️ Needs Input

- Deployment instance count and consistency target.
- Cache keys/values, TTL, capacity.
- Redis/Memcached/JetCache runtime environment.

### ❌ Out of Scope

- Treating the cache as a database.
- Claiming a local Cache supports cluster idempotency.
- Flushing production caches without authorization.

## Workflow

### Step 1: Define data authority and invalidation policy

Decide what the source of truth is, when cached entries are invalidated, and what happens on a miss. The cache never becomes the authority; the invalidation policy is part of the design, not an afterthought.

### Step 2: Choose local, distributed, or multilevel

Match the consistency requirement to the implementation: Caffeine/Guava/Hutool for single-JVM speed, Lettuce/Jedis/Redisson for shared state, JetCache for multilevel. No local cache provides cross-instance consistency — decide before writing code.

### Step 3: Verify get/put/invalidate, TTL, and failure paths

Test the basic operations, TTL units and edge values, concurrent access, and what happens when the backend is down. Semantics differ per implementation and must be tested, not assumed.

### Step 4: Prove CAS contention if idempotency is required

Run the cluster test: two independent clients contending for the same key via `AtomicCache`/`CasCache`, exactly one winner, re-acquisition after TTL, and network-failure behavior. Single-JVM tests prove nothing about cross-instance CAS.

### Step 5: Add observability and degradation

Wire `CacheStats` plus business-level metrics, set capacity bounds, and define the degradation strategy — including the explicit rule that a cache outage must not be reported as business success.

## Gotchas

- Caffeine-backed idempotency passing on a single instance and silently duplicating on two — local caches have no cross-instance view, and every single-JVM test stays green.
- A get-then-put sequence standing in for CAS — between the two calls another instance can win; the atomic `CasCache`/`AtomicCache` contracts exist precisely because that window is real.
- Cache keys without a tenant segment — a shared key lets one tenant read another's entry, and the bug only appears with the second tenant.
- `REDIS_OBJECT_MAPPER` enabling `DefaultTyping` — safe for trusted cache data only; pointing it at external input turns deserialization into a code-execution vector.
- Locks that are acquired but not released on the exception path — the holder crashes, the lock lives until TTL, and every subsequent request blocks or fails in the meantime.
- Redis unavailable and the code returning "success" anyway — the operation did not happen; silent success converts an outage into invisible data loss.
- Assuming TTL semantics are uniform — zero, negative values, and precision behave differently per implementation and must be tested per provider.

## Deep Reference

- [Provider Matrix](references/provider-matrix.md)
- [CAS and Idempotency](references/cas-and-idempotency.md)
- [Serialization and Keys](references/serialization-and-keys.md)
- [Testing](references/testing.md)
- [Anti-Patterns](references/anti-patterns.md)
- [Deep FAQ](references/faq-deep.md)

## Privacy and Security

Cache keys, values, and logs must not expose tokens, passwords, ID numbers, phone numbers, or tenant secrets. 本技能不访问、不收集、不存储、不传输任何用户数据、凭据或密钥；缓存键值示例仅使用脱敏的虚构数据。

## Quick Start

- "Use `$ddd4j-cache` to analyze the implementation and configuration my current project should adopt."
- "Use `$ddd4j-cache` to review existing usage against the current source."
- "Use `$ddd4j-cache` to return an implementation choice, evidence state, and remaining risk."

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
