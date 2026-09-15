# Example 2 — Duplicate-utility and mapper-misuse review (read-only)

## Prompt

> A teammate said our codebase has "utility sprawl". Do a read-only pass: what are we hand-rolling that ddd4j Kit already ships, and are we misusing any Kit APIs?

## What the skill should do

1. Stay read-only — inventory, no deletions.
2. Find hand-rolled helpers duplicating `StrKit`, `CollKit`, `ArrayKit`, `IdKit`, `DateKit`, or `ReflectKit` functionality.
3. Find every use of `REDIS_OBJECT_MAPPER` and classify the input as trusted cache data or external.
4. Find `BeanKit` copy call sites that cross a domain/PO boundary where explicit mapping is required.
5. Find swallowed-exception patterns around Kit calls (`catch → return null/false`).

## Expected output

| Finding | Location | Class |
|---|---|---|
| Private `StringUtils.isBlank` reimplementation (37 lines) | `common/StringHelper.java` | duplicate of `StrKit` |
| `REDIS_OBJECT_MAPPER.readValue(...)` on an inbound webhook payload | `WebhookHandler.java:52` | misuse — untrusted input through typing-enabled mapper |
| `BeanKit.copy(order, OrderPO.class)` across the domain boundary | `OrderAssembler.java:30` | implicit mapping — needs explicit mapper |
| `catch (Exception e) { return false; }` around `JsonKit.parse` | `FlagDecoder.java:18` | swallowed exception |

Clean: no duplicate collection helpers found. Evidence: SOURCE only — no code executed.

## Failure the skill must avoid

Reporting only the cosmetic duplicates and missing the webhook deserialization through the Redis mapper. Sprawl is annoying; the typing-enabled mapper on untrusted input is the actual security finding.
