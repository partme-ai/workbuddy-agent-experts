# Example 2 — Observability configuration review (read-only)

## Prompt

> We keep finding out about outages from customers. Read-only review of the observability setup: probes, metrics, tracing — where are the blind spots?

## What the skill should do

1. Stay read-only; findings with severity, not patches.
2. Fix the line, then read the Actuator, monitor, metrics, and OTel AutoConfiguration and Properties plus any user-declared telemetry beans.
3. Check the liveness/readiness split and what readiness actually aggregates.
4. Check metric registration against real operations and trace export targets against the actual backend.
5. Check exposure settings, off switches, and exporter lifecycle for shutdown losses.

## Expected output

| Check | Finding | Severity |
|---|---|---|
| Liveness | includes DB health → DB blip restarts all pods | Critical |
| Readiness | aggregates DB only; MQ and cache missing | High |
| Metrics | endpoints respond, but no domain counters registered | High |
| Tracing | exporter targets a staging collector URL in prod config | Critical |
| Exposure | health fully exposed unauthenticated on this line | Medium |
| Shutdown | batching exporter lacks idempotent close → deploy-time loss | Medium |

Evidence: SOURCE read on line <L>. No behavior tests executed — read-only review.

## Failure the skill must avoid

Concluding "observability is fine, the endpoints all answer" from a probe sweep. The blind spots that page customers — misdirected exporters and counters that never registered — are only visible by reading what each bean actually aggregates and targets.
