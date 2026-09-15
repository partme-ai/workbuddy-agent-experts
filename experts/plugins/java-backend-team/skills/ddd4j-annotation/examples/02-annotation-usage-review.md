# Example 2 — Annotation usage review (read-only)

## Prompt

> Audit our usage of ddd4j annotations across the module. I suspect we slapped some on without wiring anything behind them.

## What the skill should do

1. Stay read-only — produce findings, not patches.
2. Enumerate every ddd4j annotation occurrence and classify by family (ddd/Contract, cqrs, api, orm).
3. For each occurrence, locate the consumer: registrar, interceptor, `IdempotencyGuard`, repository hook, or event publisher.
4. Flag every annotation that has no consumer, and every domain class that references PO annotation packages.
5. Report which checks passed, which failed, and which could not be verified without running tests.

## Expected output

| Location | Annotation | Consumer found | Verdict |
|---|---|---|---|
| `OrderPO.java:12` | `@BizKey` | repository unique-key hook | OK |
| `PaymentResource.java:30` | `@ApiIdempotent` | none — no `IdempotencyGuard` registered | VIOLATION |
| `ShipmentPO.java:8` | `@OnUpdate` | interceptor present in data adapter | OK |
| `Order.java:4` | imports `..orm.DomainField` | domain referencing PO metadata | VIOLATION |

Plus a summary of clean areas and an explicit `NOT RUN` note for any consumer that requires a live request to verify.

## Failure the skill must avoid

Declaring the audit clean after only grepping for annotation names. Presence tells you nothing; the review exists to find annotations whose consumers were never wired.
