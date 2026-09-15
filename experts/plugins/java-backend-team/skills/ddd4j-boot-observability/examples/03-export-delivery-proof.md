# Example 3 — Telemetry delivery proof at the backend

## Prompt

> The OTel agent logs say everything is exported. Our Grafana says otherwise. Figure out where the telemetry actually goes, with evidence.

## What the skill should do

1. Treat "SDK logs are clean, backend is empty" as an export-path defect until proven otherwise — initialization logs never prove delivery.
2. Fix the line and read the assembled exporter configuration: target endpoint, protocol, and batching settings.
3. Compare the configured target with the intended backend; check for environment overrides that silently redirected the endpoint.
4. Run an end-to-end test: generate a marked span and a marked metric, then query the collector/backend for their arrival.
5. Report where the data actually lands, the fix, and re-verify delivery end to end.

## Expected output

```
Symptom: OTel SDK logs show successful exports; backend empty.

Source read (line 3.x):
  configured exporter endpoint: otel-collector.staging.internal:4317
  intended (prod):              otel-collector.prod.internal:4317
  cause: env overlay never overrode the staging default.

End-to-end proof after fix:
  marked span  → visible in collector → backend   PASS
  marked metric → visible in backend              PASS
  (a delivery claim without a backend-side check would be unproven)

Evidence: SOURCE + delivery TEST RUN verified at the collector.
```

## Failure the skill must avoid

Closing the ticket because the agent logs show "export success". The SDK was successfully exporting to the wrong collector the entire time — only a backend-side arrival check distinguishes delivered from discarded.
