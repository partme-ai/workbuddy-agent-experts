# Example 2 — Read-only ignore-rule and exemption audit

## Prompt

> Before our SOC2 review: audit every tenant ignore rule and exempt table in our service. I want justification per rule, read-only.

## What the skill should do

1. Stay read-only — inventory, not changes.
2. Enumerate every ignore rule and exempt table with its file path and the condition that triggers it.
3. For each rule, test the condition's breadth: does it fire only for the intended system operation, or for anything that happens to match (empty tenant, system user, specific thread)?
4. Check that `TenantContextHolder` state set by background operations is cleared on every exit path.
5. Produce the inventory with per-rule justification and flag rules that cannot be justified.

## Expected output

| Rule / exemption | Condition | Intended for | Verdict |
|---|---|---|---|
| audit_log exempt | table list | shared system log | OK |
| ignore when user = svc-batch | user check only | batch job | TOO BROAD — fires for any svc-batch request |
| ignore when tenant empty | empty check | startup jobs | RISK — swallows missing tenant on real requests |

Evidence: SOURCE only. Runtime cross-tenant probes NOT RUN — listed as the follow-up.

## Failure the skill must avoid

Accepting rules because they "have a comment saying system ops". The SOC2-relevant question is the condition's actual breadth — an empty-tenant or user-based condition that also matches ordinary requests is a silent cross-tenant read path.
