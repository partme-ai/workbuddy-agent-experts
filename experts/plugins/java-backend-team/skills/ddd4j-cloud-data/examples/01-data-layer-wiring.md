# Example 1 — Wiring the data layer for a new service

## Prompt

> New ddd4j-cloud service on the 2023.0.x line: MySQL, MyBatis, tenant-filtered tables, and one flow that spans two services. Wire the data layer.

## What the skill should do

1. Fix the combination with `ddd4j-cloud-version-selection`, then pick the access stack from the line's data extensions — not from whatever library is newest.
2. Wire repositories through the ddd4j `Repository` SPI with the MyBatis adapter registered by the data extension.
3. Decide the transaction strategy: local `@Transactional` inside the service, Seata for the two-service flow — and state where each applies.
4. Enable tenant-aware filtering in the data layer, with the exemption list owned by the tenant rules (route details to `ddd4j-cloud-tenant`).
5. Order migrations so tenant columns exist before filtering activates, and specify the real-MySQL tests to run.

## Expected output

```
Stack: MySQL + MyBatis adapter (cloud data extension, <config keys>)
Repository: domain depends on Repository SPI; adapter registered by extension
Transactions: local for single-service flows; Seata global for
  order→inventory flow (propagation stated per hop)
Migrations: V<n> adds tenant_id → filtering enabled only after V<n> runs

Tests required: real-MySQL round-trip, Seata commit+rollback across both
services, migration up/down. Evidence: pending run.
```

## Failure the skill must avoid

Enabling tenant filtering in the same migration that adds the column (bootstrapping breaks), or assuming the Seata annotation alone makes the cross-service flow transactional without testing the rollback path against both real services.
