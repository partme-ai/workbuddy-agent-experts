# Workflow — ddd4j-javalin Data Integration

A canonical end-to-end flow for wiring data access into a Javalin service.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the line.
- Locate the data module, EMF wiring, and database tests.

## Step 2 — Select the access stack

- Choose MyBatis or JPA/PostgreSQL and confirm Repository and transaction wiring.
- Confirm EventStore, Projection, and Outbox initialization order.

## Step 3 — Manage lifecycle

- Confirm the EntityManagerFactory, schedulers, and listeners have owners.
- Verify drain and idempotent close, and readiness contribution of the database dependency.

## Step 4 — Test

- Run real database round-trips: transactions, conflicts, Projection advancement, Outbox delivery.
- Cover startup failure and rollback behavior.

## Step 5 — Report

Produce a single report containing:

- Chosen stack with configuration keys and connection handling.
- Lifecycle owners and shutdown order.
- Tests executed and evidence state per tier.
- Risks with proposed fixes and missing inputs.
