# Example 5 — Metrics endpoint answers, backend shows nothing

## Prompt

> Our metrics endpoint returns a wall of numbers, but the monitoring dashboard has been empty since the upgrade to the new ddd4j line. The endpoint literally works. Where did our metrics go?

## What the skill should do

1. Split the question in two: the local registry (what the endpoint prints) versus the exported registry (what the backend scrapes/receives). The upgrade can rewire one without the other.
2. Read the assembled metrics configuration on the new line: which registry the boot module exports, and whether a user-declared registry bean replaced the default.
3. Check for the silent-swap pattern: a `@ConditionalOnMissingBean` default now backing off because a leftover custom registry bean exists — the endpoint prints the custom registry while the exporter reads the (empty) default.
4. Verify with a marked increment: perform a real operation and confirm the counter moves in both the endpoint output and the backend.
5. Fix at the assembly level (remove the shadowing bean or point the exporter at the active registry) and re-verify delivery.

## Expected output

```
Symptom: /metrics populated; dashboard empty since line upgrade.

Read from source:
  boot module exporter targets: the line's default registry
  application declares: a custom MetricsRegistry bean (pre-upgrade
  leftover) → default backed off via @ConditionalOnMissingBean
  result: endpoint prints the custom registry; exporter scrapes the
  empty default one.

Marked increment check:
  counter moves in /metrics output      PASS (custom registry)
  counter moves in backend              FAIL (default registry, empty)

Fix: remove the leftover registry bean (or bind the exporter to the
active registry); re-run the marked increment against the backend. PASS.

Evidence: SOURCE + delivery TEST RUN.
```

## Failure the skill must avoid

"Fixing" the dashboard by pointing Grafana at the local endpoint dump. The exported pipeline is still empty — alerts still fire on nothing — and the shadowing bean keeps biting every new metric.
