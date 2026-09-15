# Workflow — ddd4j Messaging Implementation

A canonical end-to-end flow for standing up ddd4j messaging.

## Step 1 — Confirm the source of truth

- Identify the broker in use (or the deployment constraints that constrain the choice).
- Decide delivery semantics: at-most-once or at-least-once, ordering needs.

## Step 2 — Select the adapter

- Match the requirement to the broker matrix.
- Verify the module and artifacts exist in the current maintenance line.

## Step 3 — Configure producer and consumer

- Set topic/tag/group/namespace, serialization, and header mapping.
- Mark listeners required or optional.

## Step 4 — Implement reliability

- Ack after successful business processing; nack with policy-driven requeue.
- Add backoff, retry limits, and dead-letter routing.
- Make consumers idempotent by message/event id; use an Outbox for send/transaction bridging.

## Step 5 — Implement lifecycle

- Follow validate → producer init → consumer init → listener register → ready.
- On partial failure, roll back in reverse order; make close idempotent.
- Let required-listener failure block startup and degrade readiness for optional ones.

## Verify

- Run Testcontainers round-trips: publish/consume, headers, ack, nack/retry, duplicates, recovery, close.
- Mark Docker-unavailable suites BLOCKED/SKIPPED, never PASS.
- Produce a report with broker choice, evidence state, and remaining risk.
