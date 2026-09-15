# Workflow — Implementing a Domain Aggregate

A canonical end-to-end flow for building or reviewing a ddd4j aggregate.

## Step 1 — Confirm the maintenance line

- Identify the current branch (`1.0.x`, `2.0.x`, or `3.0.x`).
- Read the active `AggregateRoot`, `Command`, `Query`, `Repository`, and `DomainEvent` source.
- Note the JDK, Maven, and POM Model for the line.

## Step 2 — Choose the persistence mode

- Active Record: snapshot persistence with explicit `save()`.
- Event Sourcing: persist `pullDomainEvents()` and replay via `loadFromHistory`.
- Decide once per aggregate. Document the choice in the SKILL.md entry or the file header.

## Step 3 — Model the aggregate

- Extend `AggregateRoot<ID>`; the identifier implements `Serializable`.
- Keep all mutations inside the aggregate body; never mutate state from outside.
- Register domain events with `registerEvent(...)` and apply them in `@EventHandler` methods.
- Preserve a no-arg constructor on every event subclass.

## Step 4 — Wire the contract

- Define a `Command` interface and a `CommandExecutor` for write paths.
- Define a `Query<M>` for read paths and opt into PO fields with `persistence(P.class)` only when needed.
- Domain depends only on `Repository`; concrete data adapters register implementations.

## Step 5 — Test the chain

- Aggregate invariant tests (state transitions, error paths).
- Event replay tests (`loadFromHistory` produces the same state).
- Command result tests (success, business failure, infrastructure failure).
- Context cleanup tests (`ThreadContext` released on success, exception, and async completion).
- Cross-line build test for the same code on at least one other maintenance line.
