# Example 1 — Instrumenting a projection with OpenTelemetry

## Prompt

> Our inventory projection is a black box — we find out it's behind only when support tickets pile up. Instrument it properly for ddd4j 2.0.x with OpenTelemetry.

## What the skill should do

1. Confirm the port surface for the line: `ProjectionMetrics` / `NoopProjectionMetrics` in core, `OpenTelemetryProjectionMetrics` as the adapter.
2. Define the series: run success/failure, processed events count, duration, and position lag (where a reliable position source exists).
3. Fix the labels at low cardinality: projection name, outcome class — explicitly no tenant/user/message id.
4. Require the runtime binds the OTel implementation, not the Noop — and that absence of a backend degrades loudly.
5. Specify the tests: names, label sets, increments, and the exception path recording failure without advancing a pseudo-success.

## Expected output

```
Metric set (projection "inventory-projection"):
  ddd4j.projection.run.success   counter   {projection}
  ddd4j.projection.run.failure   counter   {projection, error_class}
  ddd4j.projection.processed     counter   {projection}
  ddd4j.projection.duration      timer     {projection}
  ddd4j.projection.position_lag  gauge     {projection}   (source permitting)

Excluded labels: tenant, user, message id (cardinality + PII rule).
Runtime binding: OpenTelemetryProjectionMetrics registered; Noop only behind
an explicit degradation flag.

Tests: increment on success; failure counter increments AND position does not
advance on exception; Noop path flagged degraded. Status: NOT RUN.
```

## Failure the skill must avoid

Emitting a single "events handled" counter with the exception swallowed inside. Success-only metrics read 100% healthy straight through the outage that generated the support tickets.
