# Workflow — ddd4j-cloud Data Integration

A canonical end-to-end flow for wiring data access in a Spring Cloud service.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combination.
- Locate the cloud data extensions and database tests.

## Step 2 — Select the access stack

- Choose datasource, MyBatis, or JPA and confirm Repository wiring.
- Decide transaction strategy: local or Seata, with tenant-aware isolation.

## Step 3 — Wire migrations and lifecycle

- Confirm migration execution order and tenant-aware filtering.
- Confirm datasource owners, failure rollback, and idempotent close.

## Step 4 — Test

- Run real database round-trips: transactions, tenant isolation, migration up/down.
- Cover cross-service transactions where Seata is used.

## Step 5 — Report

Produce a single report containing:

- Chosen stack with configuration keys.
- Transaction and tenant strategy with owners.
- Tests executed and evidence state per tier (marking NOT VERIFIED where external behavior lacks proof).
- Risks with proposed fixes and missing inputs.
