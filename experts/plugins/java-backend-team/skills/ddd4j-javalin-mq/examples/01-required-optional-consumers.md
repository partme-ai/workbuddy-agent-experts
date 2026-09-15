# Example 1 — Required and optional consumers with explicit readiness

## Prompt

> We have two consumers on our 7.2.x service: the payment-events one is critical, the analytics one is nice-to-have. Wire them so an analytics outage doesn't take us down, but a payment outage does.

## What the skill should do

1. Confirm the line (7.2.x → Javalin 7.2/ddd4j 3/JDK 21/Maven 4) and read the MQ module's listener registration and readiness contracts.
2. Register the payment-events `MQClient` as a required lifecycle participant: its failure at startup blocks startup; its failure later degrades readiness to NOT READY.
3. Register the analytics consumer as optional: its failure yields an explicit DEGRADED readiness status, never a silent READY.
4. Write the failing contracts first — broker down ⇒ required blocks startup; optional broker down ⇒ readiness DEGRADED with the participant named.

## Expected output

```java
runtime.register(MQClient.required(paymentConsumer));  // failure blocks startup/readiness
runtime.register(MQClient.optional(analyticsConsumer)); // failure ⇒ explicit DEGRADED
```

Evidence block:

```
| Case                              | Expected                    | State |
|-----------------------------------|-----------------------------|-------|
| Payment broker down at startup    | startup fails, cause named  | PASS (executed) |
| Analytics broker down at startup  | startup succeeds            | PASS (executed) |
| Analytics broker down at runtime  | readiness = DEGRADED (analytics) | PASS (executed) |
| Payment broker down at runtime    | readiness = NOT READY       | PASS (executed) |
```

## Failure the skill must avoid

Registering both consumers as required "to be safe", which turns every analytics-cluster blip into a full service restart — or both as optional, which silently ships payments while the payment broker is down.
