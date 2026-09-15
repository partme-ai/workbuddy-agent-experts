# Example 2 — Read-only data layer review

## Prompt

> Review our data layer read-only before we split the monolith. We're on ddd4j-quarkus 4.0.x. I mostly care about tenant isolation and transaction boundaries.

## What the skill should do

1. Stay read-only and fix the line/SHA (4.0.x → Quarkus Platform 3.38.2 / ddd4j 3.0.x / JDK 21 / Maven 4).
2. Check the domain depends only on the `Repository` SPI — flag Panache/JPA imports inside domain classes.
3. Verify tenant isolation is enforced at the data-binding level for every query, not only the new ones.
4. Trace transaction boundaries: one transaction per command, no cross-aggregate transactions by accident.
5. Check datasource lifecycle ownership and idempotent close.

## Expected output

| Check | Finding | Verdict |
|---|---|---|
| Domain purity | `OrderRepository` (domain) imports `io.quarkus.hibernate.orm.Panache` | **VIOLATION** |
| Tenant isolation | 14/19 queries filter tenant_id; 5 legacy queries do not | **GAP** |
| Transactions | one TX per command handler | OK |
| Lifecycle | datasource owned by shutdown observer, close idempotent | OK |
| Native | entity reflection registrations present | OK |

Evidence: SOURCE read. QuarkusTest suites NOT RUN on this SHA.

## Failure the skill must avoid

Passing the review because "it compiles and the tests are green". The domain-layer ORM import and the five unfiltered legacy queries both survive any test that only exercises the new code paths.
