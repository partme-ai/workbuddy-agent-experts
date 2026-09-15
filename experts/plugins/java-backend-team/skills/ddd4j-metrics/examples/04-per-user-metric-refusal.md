# Example 4 — Boundary: per-user latency metric requested

## Prompt

> Support wants to answer "how slow is THIS customer's checkout?" from a dashboard. Just add the customer id as a label on the checkout latency metric — it's only a few hundred customers.

## What the skill should do

1. Refuse customer id as a label on two independent grounds: it is PII in the metrics store, and it is unbounded cardinality by rule — "only a few hundred today" is not a contract, and customer count grows.
2. Explain where the metrics store sits: labels are searchable/exported and often retained longer than application logs, so PII in labels outlives the request that produced it.
3. Offer the correct design: keep the metric labeled by bounded dimensions (endpoint, status family, customer tier if tiers exist), and answer per-customer questions from logs/traces with sampled correlation — traces carry identifiers by design with access control.
4. State the rule origin: the skill's privacy rule and cardinality rule both bind here; this is a standing refusal pattern, not a judgment call about this customer's count.

## Expected output

```
Refusal: customer_id as a metric label.
  - privacy rule: user identifiers must not appear in labels
  - cardinality rule: label values must be bounded by contract, not by
    current data ("a few hundred" grows and multiplies per endpoint × tier)

Correct design:
  - checkout latency labeled by {endpoint, status_family, tier}
  - per-customer investigation: trace/log lookup by customer reference,
    sampled and access-controlled, correlated to the metric's outcome class

What was produced: the label design above. The requested label was not
created.
```

## Failure the skill must avoid

Adding the label "temporarily" because the number is small. The exception eats the rule: per-entity labels are unbounded by definition, and the metrics store becomes a PII warehouse nobody remembers approving.
