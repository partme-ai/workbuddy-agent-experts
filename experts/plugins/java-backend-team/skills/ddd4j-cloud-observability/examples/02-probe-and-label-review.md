# Example 2 — Read-only probe and metrics review

## Prompt

> Audit our observability setup read-only. Ops says our dashboards exploded in cardinality last month and one pod restarted during a Nacos outage — connect the dots if you can.

## What the skill should do

1. Stay read-only — inspect probe definitions, metric labels, log fields, and trace propagation.
2. Check liveness vs readiness separation — liveness must not consult external services (the likely restart cause).
3. Inspect metric labels for high-cardinality fields: user ids, tenant ids, request ids, raw URLs.
4. Check trace propagation covers async, Reactor, and Feign paths, and that log fields are redacted.
5. Report findings with the configuration keys involved and the evidence needed to confirm each.

## Expected output

| Area | Finding | Impact |
|---|---|---|
| Liveness | `/health/liveness` pings Nacos | registry blip → pod restart (matches ops incident) |
| Metrics | `http_requests_total` labeled with `user_id` | cardinality explosion (matches dashboards) |
| Traces | async handler path loses trace parent | fragmented traces under load |
| Logs | request logs include full tenant name | redaction gap |

Evidence: SOURCE + config read. Live probe drill NOT RUN — required to confirm liveness behavior.

## Failure the skill must avoid

Treating the two ops complaints as unrelated. The liveness-wired-to-Nacos finding explains the restart, the label finding explains the cardinality explosion — and both are the classic misconfigurations this review exists to surface.
