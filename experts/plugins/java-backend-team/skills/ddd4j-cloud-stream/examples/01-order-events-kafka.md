# Example 1 — Publishing order events to Kafka with tenant headers

## Prompt

> Our order service (Spring Cloud, ddd4j) must publish order events to Kafka; the billing service consumes them and needs the tenant to apply pricing rules. Wire it.

## What the skill should do

1. Fix the combination with `ddd4j-cloud-version-selection`, then use the line's stream extension and `BindingNamingContributor` naming rules.
2. Write the binding map explicitly: function name → binding name → physical Kafka topic, so the three name layers never blur.
3. Configure the producer to write Context/Tenant into message headers, and the consumer to restore them onto its processing thread.
4. Set consumer ACK and retry plus dead-letter policy for poison messages.
5. Specify the verification: real publish/consume, tenant present on the consumer side, nack/retry path exercised.

## Expected output

```
Binding map:
  function: orderEventPublisher → binding: orderEvents-out-0
            → destination: orders.events (Kafka)
  function: billingConsumer     → binding: orderEvents-in-0
            → destination: orders.events

Headers: tenant + context written at publish, restored on consume
Reliability: manual ACK, 3 retries with backoff, DLQ after

Verification pending: real broker round-trip, nack→retry→DLQ path.
```

## Failure the skill must avoid

Declaring "done" when the app starts and logs the binding. Without the explicit three-name map and a real consume-side assertion that the tenant header arrived and was restored, the events may be flowing to a differently-named topic or arriving without tenant context.
