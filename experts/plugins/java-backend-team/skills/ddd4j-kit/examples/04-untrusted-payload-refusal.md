# Example 4 — Boundary: Redis mapper on untrusted input

## Prompt

> Our partner sends us JSON with type hints so we can rebuild their object graph — `["@type":"com.partner.Model", ...]`. The Redis mapper in `JsonKit` already does polymorphic binding, so we'll reuse it to parse their payloads. Fine, right?

## What the skill should do

1. Refuse the reuse: `REDIS_OBJECT_MAPPER` enables `DefaultTyping` and is contractually restricted to trusted cache data the application itself wrote.
2. Explain the attack it opens on external input: a crafted `@type` instructs the deserializer to instantiate arbitrary classes — a known remote-code-execution class, not a theoretical risk.
3. Offer the correct path: parse partner payloads with `DEFAULT_OBJECT_MAPPER` into an explicit DTO contract, and treat any typing behavior as forbidden at the trust boundary.
4. Note the second misuse this uncovers: events must use `EventPayloadSerializer`, never either global mapper — worth confirming the caller isn't about to repeat the mistake there.

## Expected output

```
Refusal: REDIS_OBJECT_MAPPER is for trusted cache data only. Its
DefaultTyping honors @type metadata, so partner-controlled JSON becomes
arbitrary class instantiation on your classpath.

Correct contract for partner payloads:
  - parse with DEFAULT_OBJECT_MAPPER into a fixed partner DTO
  - validate fields explicitly; no type metadata honored
  - if the partner format truly requires polymorphism, model it with an
    explicit discriminator field in your own DTO, not runtime typing

Related check: EventStore serialization stays on EventPayloadSerializer —
neither global mapper belongs there.
Evidence: SOURCE (mapper contracts on the current line).
```

## Failure the skill must avoid

Approving the reuse because "the mapper already supports it." Capability is not authorization — the mapper's polymorphic power is precisely what must never face untrusted bytes.
