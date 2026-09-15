# Example 4 — Cluster-wide monitoring stack request

## Prompt

> Set up Prometheus, Grafana dashboards, and alert rules for our whole Kubernetes cluster — and while you're at it, decide our SLO thresholds.

## What the skill should do

1. Say plainly: do not use this skill for cluster-wide monitoring infrastructure — Prometheus/Grafana deployment, dashboards, and alert routing are generic infrastructure tooling with no ddd4j coupling (no install command applies).
2. Draw the boundary precisely: this skill covers the service-side observability of ddd4j-cloud — the monitor/nacos/sentinel extensions, probes, trace propagation, label discipline.
3. Offer the service-side piece that is in scope: exposing metrics correctly, keeping labels low-cardinality and redacted, wiring readiness to real dependencies.
4. Route the SLO threshold decision to the platform/SRE owner — it is an organizational commitment, not a skill output.
5. If the cluster tooling later needs ddd4j-specific metrics from these services, that contract stays in this skill's scope.

## Expected output

```
Out of scope (generic infra, no ddd4j install):
  - Prometheus/Grafana deployment, dashboards, alert routing
  - SLO threshold decisions (platform/SRE owner)

In scope (this skill):
  - Service-side: monitor/nacos/sentinel extension configuration
  - Metrics exposed with low-cardinality, redacted labels
  - Readiness aggregating real dependencies; liveness independent
  - Trace propagation across sync/async/Reactor/Feign

Handoff: none needed for the infra ask — use your platform tooling
chain; reconvene on the service-side contract above.
```

## Failure the skill must avoid

Inventing SLO thresholds and dashboard layouts "since we're already talking about observability". Those are organizational commitments outside the skill's contracts, and bundling them in hides the service-side items that actually are verifiable here.
