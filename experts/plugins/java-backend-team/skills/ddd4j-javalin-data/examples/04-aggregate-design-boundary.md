# Example 4 — Designing the aggregate and repository contract

## Prompt

> Before you wire the database: sketch the Order aggregate with its `Repository` interface for us, and decide whether events should be stored in the same table as state.

## What the skill should do

1. Recognize the boundary: aggregate modeling, `Repository` SPI signatures, and event storage strategy are `ddd4j-core` contracts — framework-agnostic and shared by all runtimes.
2. Hand off the design to `ddd4j-core`, naming exactly what moves: `AggregateRoot` mode choice (Active Record vs Event Sourcing), `Repository<M, ID>` shape, `DomainEvent` persistence semantics.
3. Keep the Javalin-specific half for this skill: once the contracts exist, wire their MyBatis/JPA implementations, EMF ownership, and readiness contribution.
4. Make the split explicit so the team knows which skill answers follow-up design questions.

## Expected output

```
Routing (not a refusal of the goal):

  Aggregate design, Repository SPI, event storage semantics
    → ddd4j-core
    Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-core

  This skill then takes the Javalin side (6.7.x/7.1.x/7.2.x):
    - MyBatis/JPA implementation of the agreed Repository
    - EMF/EventStore/Projection/Outbox lifecycle ownership + readiness
    - Real-database round-trip tests on the line's toolchain
```

## Failure the skill must avoid

Sketching a bespoke `OrderRepository` with JPA-flavored signatures "while we're at it". Repository contracts belong to the core SPI; inventing them in a runtime adapter couples every future runtime to one Javalin module's preferences.
