# Example 1 — Full observability setup

## Prompt

> New service going to production on Boot 3. We need proper probes for k8s, business and JVM metrics, and distributed tracing to our OTel collector. Set it up through ddd4j-boot.

## What the skill should do

1. Fix the maintenance line, then read the Actuator, monitor, metrics, and OTel AutoConfiguration and Properties on that line.
2. Separate liveness from readiness: liveness reflects the process only; readiness aggregates the real dependency checks.
3. Wire metrics so domain counters increment, and the OTel tracing pipeline with the collector as the export target.
4. Give exporters explicit owners with idempotent close, and give every observability feature a real off switch.
5. Test delivery: probe responses under dependency failure, metric increments on real operations, and spans confirmed at the collector.

## Expected output

```
Observability set (line 3.x):
  liveness  → process only; no dependency checks folded in
  readiness → aggregates DB, MQ, cache health indicators
  metrics   → JVM + domain counters via the boot metrics assembly
  tracing   → OTel exporter → collector endpoint from Properties
  logging   → trace IDs correlated into log format

Delivery tests:
  readiness flips when DB check fails     PASS
  domain counter increments on operation  PASS
  spans present at the COLLECTOR          PASS (verified backend-side,
                                          not just SDK logs)
  shutdown: exporter closed, final window delivered  PASS

Evidence: SOURCE + behavior TEST RUN. CI: NOT RUN.
```

## Failure the skill must avoid

Wiring dependency checks into liveness. It looks like extra safety, but a database blip then fails liveness, kubelet kills every pod, and a brief dependency hiccup becomes a full-service restart storm.
