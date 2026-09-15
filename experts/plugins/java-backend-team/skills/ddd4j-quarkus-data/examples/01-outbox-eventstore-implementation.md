# Example 1 — Transactional Outbox with EventStore

## Prompt

> We're on ddd4j-quarkus 3.3.x with Postgres. Orders must publish domain events transactionally — no lost events, no phantom events. How do we build this?

## What the skill should do

1. Fix the line (3.3.x → Quarkus Platform 3.37.4 / ddd4j 2.0.x / JDK 17 / Maven 3) and read the data adapters in that checkout.
2. Recommend the stack: Panache or JPA for the Outbox table plus the EventStore, sharing the same transaction boundary as the aggregate write.
3. Persist exactly what `pullDomainEvents()` produced — never double-write snapshots and events for the same aggregate.
4. Define the relay as a periodic/observed task with per-row transactional claims, so a crashed relay leaves rows claimable, not lost.
5. Define the tests: QuarkusTest against Testcontainers Postgres — commit-and-publish, rollback-and-no-publish, relay crash recovery.

## Expected output

```
Stack: JPA (Panache entities in the data adapter) + ddd4j EventStore + Outbox table.
Transaction boundary: one TX = aggregate write + EventStore append + Outbox insert.
Relay: poll Outbox with claim-then-publish per row; failed publishes retry with
backoff, then dead-letter.

Tests (Testcontainers Postgres):
  - commit → events in EventStore + Outbox rows present
  - rollback → neither present
  - relay crash mid-publish → row remains claimed-or-claimable, republished once

Evidence: SOURCE + TEST(Testcontainers). Native NOT RUN — entity reflection audit pending.
```

## Failure the skill must avoid

Publishing events over the broker inside the same request *before* the transaction commits — a rollback then leaves phantom events, and a broker outage loses them. The Outbox exists precisely to couple publication to the committed write.
