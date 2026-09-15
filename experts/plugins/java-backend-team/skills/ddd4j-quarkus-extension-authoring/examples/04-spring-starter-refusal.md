# Example 4 — Spring Boot starter request

## Prompt

> We love this extension approach. Can you write the equivalent Spring Boot starter? Just reuse the Processor and Recorder code — how different can it be?

## What the skill should do

1. Decline to reuse the Processor/Recorder code: those are Quarkus build-time model artifacts and have no meaning inside Spring Boot's runtime auto-configuration model.
2. Name the boundary: BuildItems and recorders execute during Quarkus application build; Spring Boot starters wire beans at runtime through auto-configuration classes — the two models should not be mixed.
3. Hand off to `ddd4j-boot-extensions` for the Spring Boot equivalent, and `ddd4j-boot-version-selection` if the Boot line is not yet chosen.
4. Keep what is portable: the SPI implementation in the runtime module can be shared; only the registration layer differs.
5. Do not fabricate starter code here — do not use this skill to author Spring artifacts.

## Expected output

```
Boundary: Processor/BuildItem/Recorder are Quarkus build-time artifacts; a Spring
Boot starter cannot reuse them — its registration runs at application startup via
auto-configuration, not at build time.

Handoff: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-extensions

Portable part: the SubjectProvider SPI implementation in the runtime module can be
shared by both adapters; the registration layer must be rewritten per runtime.
```

## Failure the skill must avoid

Copying the Recorder into a Spring `@Configuration` class "as-is" and shipping it. The build-time/runtime mismatch means the code either never runs or wires at the wrong lifecycle phase.
