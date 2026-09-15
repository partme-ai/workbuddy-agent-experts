# Workflow — ddd4j Metrics Instrumentation

A canonical end-to-end flow for instrumenting ddd4j with metrics.

## Step 1 — Confirm the source of truth

- Identify the modules to instrument and the observability backend.
- Confirm the naming convention and SLO/alerting targets.

## Step 2 — Locate the ports

- Find ProjectionMetrics/NoopProjectionMetrics in core and OpenTelemetryProjectionMetrics in the adapter.
- Confirm the runtime binds the real implementation, not Noop, where observability is required.

## Step 3 — Design the metric set

- Separate success/failure, duration, and processed count.
- Choose stable low-cardinality labels; exclude tenant/user/message id and any PII.

## Step 4 — Implement and test

- Verify metric names, label sets, increments, and exception paths.
- Cover the no-backend degradation path explicitly.

## Step 5 — Wire alerting

- Derive alerts from SLOs; distinguish transient, sustained, and no-data states.
- Verify the exporter/collector receives real data end to end.

## Verify

- Run unit behavior tests, the export chain, and an alerting drill.
- Produce a report with the metric inventory, evidence state, and remaining risk.
