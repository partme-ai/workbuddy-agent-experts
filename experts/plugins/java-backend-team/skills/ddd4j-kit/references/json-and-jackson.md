# JSON and Jackson

> Collection date: 2026-09-11.

## Current Entry Points

- `io.ddd4j.kit.lang.JsonKit`
- `JsonKit.DEFAULT_OBJECT_MAPPER`
- `JsonKit.REDIS_OBJECT_MAPPER`
- `io.ddd4j.core.cqrs.eventstore.jackson.EventPayloadSerializer`

## Scenario Selection

| Scenario | Choice |
|---|---|
| Ordinary object JSON | `JsonKit` default mapper / API |
| Redis trusted object | `REDIS_OBJECT_MAPPER` |
| EventStore payload | `EventPayloadSerializer` + explicit event Class |
| Javalin 7 HTTP | the corresponding `JavalinJackson3` configuration |

`REDIS_OBJECT_MAPPER`'s `DefaultTyping` must not be used on untrusted external data. Event payloads must not depend on `@class`.
