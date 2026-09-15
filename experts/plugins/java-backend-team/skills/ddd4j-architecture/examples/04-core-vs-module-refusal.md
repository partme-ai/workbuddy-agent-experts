# Example 4 — Boundary: methodology and non-ddd4j projects

## Prompt

> We don't use ddd4j — plain Spring Boot with MyBatis. But we want your skill's module layout: can you draw our bounded contexts using the ddd4j architecture zones?

## What the skill should do

1. Decline to apply ddd4j module zones (core/kit/runtime-*/extensions) to a non-ddd4j codebase — the zones describe ddd4j's own artifact boundaries.
2. Route the actual need: generic DDD layering and bounded-context mapping is `ddd-skills` territory; Spring/MyBatis module design is generic `java-skills` / Spring skill territory.
3. Offer what remains legitimately transferable at the concept level: dependency direction and ports-and-adapters — without pretending the ddd4j module map applies.
4. Do not invent a mapping between their packages and ddd4j artifacts.

## Expected output

```
Out of scope: superimposing ddd4j architecture zones on a non-ddd4j project.
The zone table (annotation/core/kit/runtime-*/extensions) describes ddd4j's
artifact ownership; none of those artifacts exist in this codebase.

Handoff:
  - Bounded contexts, layering, event storming → generic ddd-skills.
  - Spring Boot + MyBatis module/package design → generic java-skills /
    Spring skills.

Concepts that do transfer: adapters point inward, domain stays
framework-free. Verified claims end here — no ddd4j mapping produced.
```

## Failure the skill must avoid

Drawing a "your `services/` = ddd4j runtime, your `dao/` = ddd4j data" mapping. Fabricating an equivalence between foreign packages and ddd4j artifacts produces authority-looking nonsense the skill exists to prevent.
