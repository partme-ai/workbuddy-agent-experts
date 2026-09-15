# Projection Metrics

> Collection date: 2026-09-11.

Core port: ProjectionMetrics/NoopProjectionMetrics. Implementation: OpenTelemetryProjectionMetrics.

Record at least run success/failure, processed events, duration, and position lag (where a reliable source exists). Exception paths still record failure and do not advance a pseudo-success state.
