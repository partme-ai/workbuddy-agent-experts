# Workflow — ddd4j-javalin MQ Integration

A canonical end-to-end flow for wiring messaging into the Javalin lifecycle.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the line.
- Locate the MQ module, listener registrations, and lifecycle tests.

## Step 2 — Wire listeners into the lifecycle

- Register MQClients as lifecycle participants with required or optional classification.
- Confirm required-consumer failure blocks startup; optional failure degrades readiness explicitly.

## Step 3 — Implement reliability

- Ack after successful business processing; nack with policy-driven requeue.
- Add backoff, retry limits, dead-letter routing, and message-id idempotency.

## Step 4 — Manage shutdown

- Stop receiving, drain, and close consumers/connections in reverse order.
- Confirm close is idempotent across repeated shutdowns.

## Step 5 — Verify

- Run publish/consume, ack/nack/retry, duplicate, recovery, and shutdown behavior tests.
- Produce a report with listener inventory, evidence state, and remaining risk.
