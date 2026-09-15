# Workflow — ddd4j-quarkus Data Integration

A canonical end-to-end flow for wiring data access into a Quarkus service.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the line.
- Locate ddd4j-quarkus-data and the Quarkus/Panache adapters.

## Step 2 — Select the access stack

- Choose Panache, JPA, JDBI, or R2DBC and confirm Repository wiring.
- Define composite keys, tenant isolation, and transaction boundaries.

## Step 3 — Verify lifecycle and native support

- Confirm datasource owners, startup/shutdown observers, and idempotent close.
- Confirm reflection/serialization registrations needed for native image.

## Step 4 — Test

- Run QuarkusTest suites against real databases: transactions, EventStore, Projection, and Outbox behavior.
- Cover startup failure and rollback.

## Step 5 — Report

Produce a single report containing:

- Chosen stack with configuration keys.
- Lifecycle owners and native registrations.
- Tests executed and evidence state per tier.
- Risks with proposed fixes and missing inputs.
