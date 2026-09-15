# Example 2 — Persistence boundary review (read-only)

## Prompt

> Before we onboard the next team to this service, review our persistence layer. I care about the domain/PO split and transaction boundaries, not style.

## What the skill should do

1. Stay read-only — findings, no refactors.
2. Check the domain/PO split: `AggregateRoot` subclasses must carry no persistence annotations; PO mapping must be explicit.
3. Check that `Repository` is consumed as the core port and implemented in the data adapter, not imported from the ORM.
4. Trace transaction boundaries: EventStore append, business writes, and Outbox rows share one transaction where required; Projection position and read-model writes have an explicit boundary.
5. Flag in-memory filtering patterns in mapper code that would not survive production data volumes.

## Expected output

| Finding | Location | Severity |
|---|---|---|
| `InventoryItem extends AggregateRoot<...>` annotated `@Table("inv_item")` | `InventoryItem.java:19` | high — domain equals PO |
| `OrderRepository` interface extends MyBatis `BaseMapper` in the domain module | `OrderRepository.java:11` | high — port must stay ORM-agnostic |
| EventStore append called outside the order transaction | `OrderCommandService.java:76` | critical — split commit on crash |
| Projection reads position then writes view, both inside one transaction | — | OK |

States unverified items: no query was executed, so performance and concurrency claims are SOURCE-only.

## Failure the skill must avoid

Passing the layer because "MyBatis works and tests are green." The review exists to catch the annotation-polluted aggregate and the split commit — both invisible in unit tests and both structural defects.
