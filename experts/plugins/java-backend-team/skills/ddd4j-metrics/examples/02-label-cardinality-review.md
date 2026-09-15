# Example 2 — Label cardinality and privacy review (read-only)

## Prompt

> Our metrics backend bill doubled and queries time out. Someone said our new labels might be the problem. Audit what we're attaching to ddd4j metrics.

## What the skill should do

1. Stay read-only — audit, don't relabel.
2. Enumerate every label key on every ddd4j metric series and classify: stable dimension (projection name, outcome, status family) vs unbounded value.
3. Flag high-cardinality labels: tenant id, user id, message id, order id, full URL, SQL text.
4. Flag PII-bearing labels against the privacy rule (tokens, user IDs, phone numbers in labels).
5. Estimate blast radius: for each flagged label, how many distinct values the staging data implies for production.

## Expected output

| Metric | Label | Verdict |
|---|---|---|
| `http.requests` | `status_family` | OK — bounded |
| `http.requests` | `path` | violation — full URLs with ids are unbounded |
| `projection.processed` | `tenant_id` | violation — cardinality × tenants, plus tenant data in the metrics store |
| `mq.consume` | `message_id` | violation — one series per message |
| `cache.hit` | `cache_name` | OK — bounded |

Estimate: `message_id` alone implies one series per processed message — millions/day. Verdict: drop to bounded dimensions; move identifiers to logs/traces with sampled correlation. Evidence: SOURCE + staging series counts; production cardinality NOT VERIFIED.

## Failure the skill must avoid

Recommending "raise the backend's cardinality limit." The limit exists because per-entity series are unbounded by construction; the fix is label design, not quota tuning.
