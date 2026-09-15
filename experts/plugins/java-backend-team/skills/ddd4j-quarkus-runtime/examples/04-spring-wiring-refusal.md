# Example 4 — Spring Boot wiring request for a Quarkus problem

## Prompt

> Our other services are Spring Boot. Just give me the Spring `@Bean` config for CommandBus and SubjectProvider modeled on what you showed for Quarkus.

## What the skill should do

1. Recognize the boundary: this skill owns Quarkus/Arc wiring; Spring Boot auto-configuration of the same ddd4j SPIs belongs to `ddd4j-boot-autoconfiguration`.
2. Decline to translate Arc idioms one-to-one: build-time discovery, scopes, and observers do not map to `@Bean`/component-scan semantics.
3. Confirm which runtime the project actually uses — a Spring Boot project should engage the boot skills from the start, including `ddd4j-boot-version-selection` for the line.
4. Keep the ddd4j SPI contracts portable across runtimes; only the wiring layer differs — do not use this skill's Quarkus registration code as the Spring template.
5. Offer the handoff explicitly with the install pattern.

## Expected output

```
Boundary: Quarkus Arc wiring and Spring @Bean wiring are different models
(build-time discovery vs runtime auto-configuration); this skill must not be used
as the Spring template.

Handoff:
  npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration
  (start with ddd4j-boot-version-selection if the Boot line is not fixed)

Portable part: the ddd4j SPI contracts (CommandBus, SubjectProvider) are identical;
only the registration layer changes.
```

## Failure the skill must avoid

Emitting Spring `@Configuration` code by search-and-replacing Arc annotations. The scope and lifecycle semantics differ enough that the result compiles but wires at the wrong time — for example request-scoped state captured into a singleton.
