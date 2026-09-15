# Example 2 — Data wiring review (read-only)

## Prompt

> Before we migrate the service to the new ddd4j line, do a read-only review of our data layer wiring. I suspect we have leftovers from two different access stacks.

## What the skill should do

1. Stay read-only; findings with severity, not patches.
2. Fix the line, then read the data AutoConfiguration, Properties, and every data-related bean the application declares.
3. Detect stacked access implementations — e.g. JPA and MyBatis both assembled — and determine which bean actually satisfies each SPI.
4. Check default bean guards, the off switch's scope, and resource owners (`destroyMethod`, idempotent close).
5. Check whether Flyway and the transaction manager agree on the single datasource, and what evidence exists for migration down-runs.

## Expected output

| Check | Finding | Severity |
|---|---|---|
| Access stack | JPA + MyBatis-Plus both on classpath; two `Repository` candidates, order-dependent resolution | Critical |
| Override guard | user `DataSource` bean replaces default silently | Info |
| Off switch | `data.outbox.enabled=false` still registers the dispatcher bean | High |
| Resource lifecycle | pooled `DataSource` has no explicit `destroyMethod` on this line | Medium |
| Migrations | up only; down never executed against a real database | Unverified |

Evidence: SOURCE read on line <L>. No tests executed — read-only review.

## Failure the skill must avoid

Reporting "both stacks are fine, Spring handles multiple data modules." Two candidates for one SPI resolve by bean order, which flips across Boot lines — that is a latent production defect, not a style issue.
