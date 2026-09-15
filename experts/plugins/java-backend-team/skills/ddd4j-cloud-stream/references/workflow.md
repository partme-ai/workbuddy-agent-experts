# Workflow — ddd4j-cloud Stream Integration

A canonical end-to-end flow for Spring Cloud Stream messaging.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combination.
- Locate the stream extension, BindingNamingContributor, and broker integration tests.

## Step 2 — Define bindings

- Map functions, binding names, and physical destinations per broker.
- Confirm Binder names and destination rules; do not assume cross-broker uniformity.

## Step 3 — Wire reliability

- Configure StreamBridge publishes and consumer ACK/NACK with retry and dead-letter policy.
- Propagate Context/Tenant into message headers and restore on consume.

## Step 4 — Test

- Run broker integration tests (Kafka, RabbitMQ, Pulsar, RocketMQ as applicable): publish/consume, ack/nack/retry, duplicates, recovery.
- Mark external-service gaps NOT VERIFIED or BLOCKED(upstream) where applicable.

## Step 5 — Report

Produce a single report containing:

- Binding map (function → binding → destination → broker) with configuration keys.
- Reliability settings and lifecycle owners.
- Tests executed and evidence state per tier.
- Risks with proposed fixes and missing inputs.
