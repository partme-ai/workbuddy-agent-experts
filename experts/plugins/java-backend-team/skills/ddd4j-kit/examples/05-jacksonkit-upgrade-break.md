# Example 5 — Diagnosing the 3.0.x upgrade compile break

## Prompt

> After moving our shared library to ddd4j 3.0.x, half our serialization code stopped compiling: "cannot find symbol JacksonKit". The class was everywhere last month. Did they delete JSON support?

## What the skill should do

1. Diagnose immediately: `JacksonKit` was merged away — on 3.0.x the entry point is `JsonKit` binding to `tools.jackson`; the old name is gone, not the capability.
2. Map the migration: former `JacksonKit` default mapper → `JsonKit` / `DEFAULT_OBJECT_MAPPER`; Redis-typed mapper → `REDIS_OBJECT_MAPPER` with its trusted-data restriction; event payloads → `EventPayloadSerializer`.
3. Warn about the import trap: `tools.jackson` replaces `com.fasterxml.jackson` for databind; only the annotation compatibility package keeps the `com.fasterxml.jackson.annotation` coordinates.
4. Flag the cross-line consequence: any shared module still built against older lines cannot take this migration — per-line builds required.
5. Give the verification: compile + serialization round-trip tests on the migrated module.

## Expected output

```
Diagnosis: JacksonKit was merged into JsonKit in 3.0.x; the symbol no
longer exists. JSON support is not removed.

Migration map:
  JacksonKit.defaultMapper()   → JsonKit / DEFAULT_OBJECT_MAPPER
  JacksonKit.redisMapper()     → REDIS_OBJECT_MAPPER (trusted data only)
  event payload serialization  → EventPayloadSerializer (explicit types)
  databind imports             → tools.jackson.* (not com.fasterxml.*)

Verification: compile + JSON round-trip tests on the migrated module —
NOT RUN.

Line note: do not backport these imports to 1.0.x/2.0.x branches; each line
keeps its own serialization stack.
```

## Failure the skill must avoid

"Fixing" it by adding a `JacksonKit` compatibility shim or copying 3.0.x imports onto older-line branches. Both deepen the cross-line mess the Kit skill exists to prevent.
