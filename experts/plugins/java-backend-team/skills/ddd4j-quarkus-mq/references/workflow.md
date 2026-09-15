# Workflow — ddd4j-quarkus MQ Integration

A canonical end-to-end flow for wiring messaging into a Quarkus service.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the line.
- Locate ddd4j-quarkus-mq and the broker tests.

## Step 2 — Select and register the broker

- Match the broker to delivery semantics; confirm what the current line actually supports.
- Register MQClients and listeners via CDI with explicit required/optional semantics.

## Step 3 — Implement reliability and lifecycle

- Ack after business success; nack with policy-driven requeue, retry limits, and dead letters.
- Bind startup/shutdown observers: drain, reverse-order close, idempotent close.

## Step 4 — Test

- Run Testcontainers round-trips: publish/consume, headers, ack/nack/retry, duplicates, recovery.
- Mark Docker-unavailable suites BLOCKED/SKIPPED.

## Step 5 — Report

Produce a single report containing:

- Broker and adapter choices with configuration keys.
- Listener registrations and lifecycle owners.
- Tests executed and evidence state per tier.
- Risks with proposed fixes and missing inputs.
