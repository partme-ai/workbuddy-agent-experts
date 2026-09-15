# Example 1 — Order endpoint with context, validation, idempotency

## Prompt

> Add a POST /orders endpoint on our ddd4j-quarkus 4.0.x service. It must validate input, be replay-safe when clients retry, and return stable errors.

## What the skill should do

1. Fix the line (4.0.x → Quarkus Platform 3.38.2 / ddd4j 3.0.x / JDK 21 / Maven 4) and read `ddd4j-quarkus-web` in that checkout.
2. Bind request `Context` in a REST filter with release on success, exception, and async completion.
3. Validate the payload at the boundary and map violations to a stable 400 error body — never raw stack traces.
4. Wire replay protection through the shared CAS idempotency key (client-supplied `Idempotency-Key`), not a local map.
5. Plan the QuarkusTest matrix: normal, validation error, replay (same key), async path.

## Expected output

```java
@POST @Path("/orders")
@RolesAllowed("order:write")
public Response create(@Valid CreateOrderRequest req,
                       @Idempotent Key idempotencyKey) {
    // dispatch Command; stable error mapping for validation/conflict
}
```

Test matrix: 201 on first call; identical replay with the same key returns the
original result; different key same payload creates a second order; validation
failure → 400 with stable body; filter releases Context on all paths.

## Failure the skill must avoid

Implementing replay protection with an in-VM `ConcurrentHashMap` "because it's simpler". It passes the single-node test and duplicates orders as soon as the service runs with two replicas — the key must go through shared CAS.
