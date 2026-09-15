# EventStore

> Collection date: 2026-09-11.

**Ports**: `EventStore` / `AsyncEventStore`, `StoredEvent`, `AggregateVersionConflictException`.

**Implementations**: JDBI, JPA, R2DBC, Panache, EventStoreDB.

`append` must validate the expected version; multi-event batches must be atomic; serialization uses explicit event types. Tests must cover conflicts, rollback, concurrency, ordering, and corrupted payloads.
