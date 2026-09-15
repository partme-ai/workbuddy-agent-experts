# Example 5 — Diagnosing dashboards that stay empty

## Prompt

> We "finished" metrics last sprint — code is merged, meters are registered, tests pass. But the Grafana dashboard has been blank for a week and nobody can explain it. Where do I start?

## What the skill should do

1. Start at the highest-probability defect for this exact symptom: the runtime bound `NoopProjectionMetrics` (or a Noop for the capability) — meters "register" and record nothing.
2. Verify the binding: which `ProjectionMetrics` implementation the DI container actually resolves in the deployment profile.
3. Trace the export chain in order: meter → recorder → exporter → collector/backend; find the first hop where data stops.
4. Check the tests' assertion level — registration-only tests cannot catch a Noop binding, which is why the suite stayed green.
5. Name the remaining checks if the implementation is real: backend query, scrape interval, and the no-data vs zero distinction on the panel.

## Expected output

```
Symptom: registered meters + green tests + empty dashboards.

Hop 1 — binding: runtime resolves NoopProjectionMetrics in the prod profile
        (the OTel bean is @Profile("dev"))  ← data never recorded; ROOT CAUSE
Hop 2..4 — exporter/collector: untested while Noop bound.

Why tests passed: they assert registration, which Noop satisfies.

Fix: bind OpenTelemetryProjectionMetrics in prod (remove the profile guard or
provide a prod binding), mark Noop profiles as degraded, then re-run:
increment test → exporter assert → one panel showing real data.

Evidence: SOURCE (binding config) + NOT RUN (export chain re-verification).
```

## Failure the skill must avoid

Debugging Grafana first — datasources, intervals, panel queries. The dashboards are innocent: a Noop binding means the data never existed, and only checking hop 1 reveals it.
