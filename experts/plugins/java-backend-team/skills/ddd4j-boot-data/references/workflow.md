# Workflow — ddd4j-boot Data Integration

A canonical end-to-end flow for wiring data access through ddd4j-boot.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line.
- Locate the data AutoConfiguration, Properties, and the corresponding ddd4j-data modules.

## Step 2 — Select the access implementation

- Compare JDBC, JPA, MyBatis, and MyBatis-Plus against the project's data model.
- Confirm Flyway and transaction manager wiring.

## Step 3 — Verify wiring

- Check conditional wiring, default beans, and user Bean override points.
- Confirm the off switch truly skips assembly and resources have owners with idempotent close.

## Step 4 — Test

- Execute context tests plus database round-trips, transactions, Projection, and Outbox behavior.
- Cover migration up/down against a real database where possible.

## Step 5 — Report

Produce a single report containing:

- Chosen implementations with configuration keys.
- AutoConfiguration entry points and override points.
- Test results and evidence state (configuration, bean, behavior, CI, publish reported separately).
- Risks with proposed fixes and missing inputs.
