# Example 1 — JPA/PostgreSQL wiring with EMF lifecycle

## Prompt

> We picked JPA on PostgreSQL for our 7.1.x order service. Wire it into the ddd4j runtime so the entity manager factory doesn't leak and the DB counts toward readiness.

## What the skill should do

1. Confirm the line (7.1.x → Javalin 7.1/ddd4j 2/JDK 17/Maven 3) and read the data module's JPA support and `Repository` registration contracts.
2. Register the `EntityManagerFactory` as a single-owner lifecycle participant: created during initialization, contributing to readiness, closed idempotently during drain/shutdown.
3. Register the `Repository` implementations for the aggregates and confirm transaction boundaries wrap command execution, not HTTP handlers.
4. Provide the failing contract first: a test where PostgreSQL is unreachable must yield not-ready, and a start/stop cycle must close the EMF exactly once.

## Expected output

```java
runtime.register(new JpaLifecycleParticipant(emf)); // sole EMF owner
runtime.register(new OrderRepositoryRegistration(emf)); // Repository SPI impls

// readiness: required DB participant contributes real state
// close: guarded, idempotent; reverse-order shutdown closes EMF after users
```

Plus the contract evidence: DB-down readiness test (RED before wiring, GREEN after) and an EMF close-count test showing exactly one close per stop.

## Failure the skill must avoid

Building the `EntityManagerFactory` in a static initializer "so it's available everywhere". That gives the EMF no lifecycle owner: it never contributes to readiness and survives restarts in embedded tests, which is the leak this wiring exists to prevent.
