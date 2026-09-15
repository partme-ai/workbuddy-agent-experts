# Example 1 — Event Store on JDBI with optimistic versioning

## Prompt

> We're going event sourcing for the inventory aggregate on ddd4j 2.0.x, storing events in Postgres via JDBI. Show me how the EventStore side should look.

## What the skill should do

1. Confirm the line and the port surface: `EventStore` / `AsyncEventStore`, `StoredEvent`, `AggregateVersionConflictException`.
2. Show append with an expected-version check so a concurrent writer gets a conflict instead of a silent fork.
3. Make multi-event batches atomic — all events of one transaction append or none.
4. Serialize with `EventPayloadSerializer` and explicit event types, never the Redis object mapper.
5. Specify the test set: conflict, rollback, concurrency, ordering, corrupted payloads — against a real Postgres container.

## Expected output

An append flow: `INSERT ... WHERE aggregate_id = ? AND version = ?` inside the caller's transaction; a zero-row update raises `AggregateVersionConflictException` so the caller reloads and retries. Batch appends wrapped in the same transaction; the version increments by the batch size.

Plus the test matrix with a Testcontainers Postgres: two concurrent appends at the same expected version → exactly one succeeds; forced mid-batch failure → zero rows persisted; replay returns events in version order. Evidence: SOURCE design; container tests NOT RUN.

## Failure the skill must avoid

An "event store" that appends with `INSERT` only and no expected-version predicate. Concurrent writers both succeed, history forks silently, and the corruption surfaces weeks later during replay.
