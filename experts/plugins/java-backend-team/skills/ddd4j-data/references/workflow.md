# Workflow — Choosing and Verifying a Persistence Strategy

A canonical end-to-end flow for choosing and validating a ddd4j persistence strategy.

## Step 1 — Choose the persistence model

- Snapshot persistence with explicit `save()` for simple aggregates.
- Event sourcing when the aggregate history is the source of truth; persist `pullDomainEvents()` and replay via `loadFromHistory`.
- Do not mix both on the same aggregate.

## Step 2 — Map Domain to PO

- Keep `AggregateRoot` separate from the framework PO / Entity.
- Use `DomainObjectMapper` for explicit, reviewable mappings.
- Decide which `Query<M>` needs `persistence(P.class)` for PO fields.

## Step 3 — Pick the storage adapter

- Synchronous SQL → JDBC or JDBI.
- ORM → JPA.
- Mapper → MyBatis (native) or MyBatis-Plus (Wrapper-based).
- Reactive → R2DBC.
- Quarkus → Panache.
- Event storage → JDBI / JPA / R2DBC / Panache / EventStoreDB.
- Read model → Projection on top of any storage above.
- Reliable publish → Transactional Outbox.

## Step 4 — Define cross-cutting concerns

- Transactions: propagation, isolation, timeout.
- Tenants: tenant binding, data scope, propagation across calls.
- Encryption: at-rest and in-transit; per-field encryption where needed.
- Auditing: `OnCreate` / `OnUpdate` and operation logs.

## Step 5 — Add Projection or Outbox when needed

- Projection: define position store, scheduler, idempotent handlers.
- Outbox: business write + event + outbox row in one transaction; relay claims atomically, confirms after send, retries with backoff, dead-letters after the limit.

## Step 6 — Run real-database verification

- Use real dialect containers (PostgreSQL, MySQL, Oracle, etc.) for acceptance.
- Cover rollback, concurrency, and crash recovery.
- Verify expected-version conflict for EventStore append.
- Verify Projection commit order (cursor after view).
- Verify Outbox claim / send / confirm windows.
