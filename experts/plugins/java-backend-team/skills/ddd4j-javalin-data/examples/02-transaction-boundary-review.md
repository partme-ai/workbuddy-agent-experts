# Example 2 — Transaction boundary review

## Prompt

> Do a read-only review of our data layer on 6.7.x. The gut feeling is that transactions are in the wrong place and someone bypassed the repository SPI.

## What the skill should do

1. Stay read-only; produce findings with file and line evidence.
2. Locate transaction boundaries — confirm they wrap command execution (the business operation), not HTTP handler bodies or individual repository calls.
3. Find direct ORM usage in the web layer: `QueryWrapper`, `EntityManager`, or SQL strings inside route handlers violate the `Repository` SPI direction.
4. Check `Repository` implementations: every SPI default method the handlers rely on must be overridden by the registered adapter, or flagged as a latent `UnsupportedOperationException`.

## Expected output

| File | Line | Finding | Why it matters |
|---|---|---|---|
| `OrderController.java` | 51 | opens/commits transaction per HTTP request | Transaction boundary is the command, not the request; retries replay partial work |
| `OrderQueryService.java` | 30 | builds MyBatis `QueryWrapper` directly | Bypasses `Repository` SPI; domain depends on the ORM |
| `OrderRepositoryImpl.java` | 18 | does not override `findByStatus` default | Latent `UnsupportedOperationException` on first call |

Plus: confirmed-clean items (EMF single owner, Outbox init order) and what was not verified (no database test executed in this review).

## Failure the skill must avoid

Reporting the data layer clean because all repository calls return correct JSON. The defects are structural — wrong transaction owner, SPI bypass, unoverridden default — and each one surfaces only under failure or first use.
