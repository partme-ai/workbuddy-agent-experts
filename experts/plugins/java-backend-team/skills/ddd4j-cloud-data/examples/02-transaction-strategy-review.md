# Example 2 — Read-only transaction and lifecycle review

## Prompt

> Review our data layer before we scale up: transaction boundaries, datasource lifecycle, migration order. Read-only.

## What the skill should do

1. Stay read-only — findings, not patches.
2. Map every transaction boundary and flag work that continues across `@Async`, Reactor, or Feign hops outside the original transaction.
3. Check datasource lifecycle: who owns it, what happens on failure, and whether close is idempotent.
4. Review migration ordering against tenant filtering activation.
5. Separate proven facts (source-read) from claims needing a real-database run, and list the latter.

## Expected output

| Area | Finding | Severity |
|---|---|---|
| Transactions | payment flow calls inventory via Feign inside `@Transactional` — remote work not rollback by local tx | HIGH |
| Datasource | close called from two shutdown hooks — not idempotent | MEDIUM |
| Migrations | V12 adds tenant column, V11 already enables filter — order inverted | HIGH |

Evidence: SOURCE only. Real-MySQL reproduction and Seata rollback NOT RUN — required before sign-off.

## Failure the skill must avoid

Passing the review because "transactions are annotated everywhere". The Feign call inside a local transaction is the defect: rollback of the local transaction cannot undo the remote side, and only a real cross-service test demonstrates it.
