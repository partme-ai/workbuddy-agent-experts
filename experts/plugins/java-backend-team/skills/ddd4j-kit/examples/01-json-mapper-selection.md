# Example 1 — Choosing the right JsonKit mapper per scenario

## Prompt

> We serialize three kinds of data: HTTP response bodies, cache entries in Redis, and domain events going to our event store. Can we use one ObjectMapper for everything? It feels cleaner.

## What the skill should do

1. Refuse the single-mapper plan: ddd4j 3.0.x deliberately ships separate serialization paths per trust boundary.
2. Map each scenario: `DEFAULT_OBJECT_MAPPER` for ordinary JSON (HTTP), `REDIS_OBJECT_MAPPER` for trusted cache data (it enables `DefaultTyping`), `EventPayloadSerializer` with explicit event types for the EventStore.
3. Explain the hazard: pointing the Redis mapper at external input enables polymorphic deserialization; pointing events at the wrong mapper corrupts the store.
4. Confirm the line: 3.0.x binds `tools.jackson`; the `com.fasterxml.jackson.annotation` package exists only for Jackson 2/3 annotation compatibility.
5. Ask for the evidence tier and mark what still needs a test.

## Expected output

| Data | Mapper | Why |
|---|---|---|
| HTTP request/response | `JsonKit` / `DEFAULT_OBJECT_MAPPER` | ordinary JSON, no polymorphism |
| Redis cache entries | `REDIS_OBJECT_MAPPER` | `DefaultTyping` for round-trips of trusted own data |
| EventStore payloads | `EventPayloadSerializer` + explicit event types | stable schema, replay-safe |
| Anything from third parties | `DEFAULT_OBJECT_MAPPER` | never a typing-enabled mapper |

Evidence: SOURCE (contract read on the current line). Round-trip tests NOT RUN.

## Failure the skill must avoid

"Wiring one shared ObjectMapper everywhere" for cleanliness. That routes external payloads through a typing-enabled mapper — the exact untrusted-polymorphism hazard the JSON boundary exists to prevent.
