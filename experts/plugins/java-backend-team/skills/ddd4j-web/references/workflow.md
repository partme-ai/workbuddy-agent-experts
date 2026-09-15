# Workflow — Implementing an HTTP Endpoint

A canonical end-to-end flow for designing and verifying a ddd4j HTTP endpoint.

## Step 1 — Choose the runtime

- Identify the target maintenance line and runtime adapter (`webmvc`, `webflux`, `javalin`, `quarkus`, `micronaut`, `vertx`, `helidon`, `dropwizard`).
- Read the matching adapter source and tests.

## Step 2 — Define the contract

- Specify path, method, request / response payload, and error mapping.
- Decide which status codes are emitted (400 / 401 / 403 / 404 / 409 / 415 / 422 / 429 / 500).
- Document the idempotency scope (closed / single-instance / shared CAS).

## Step 3 — Implement binding and cleanup

- Bind Request ID, Trace ID, Tenant, and Subject at the entry point.
- Restore the previous context in `finally` and in async completion / error callbacks.
- Never let framework Context leak into the domain layer.

## Step 4 — Implement handler

- Validate input with the four ddd4j constraints.
- Translate to a domain Command or Query.
- Hand off to the runtime's Command / Query executor.
- Map domain errors back to the agreed status codes without exposing internal stack traces.

## Step 5 — Configure production controls

- CORS: explicit allowlist for origin / credentials / headers / methods.
- Limits: request size, timeout, rate limit.
- Idempotency: shared CAS in production.
- Readiness: aggregate DB, MQ, Auth, Outbox participants.

## Step 6 — Verify

- Run the web-testkit contract against the chosen runtime.
- Add cross-runtime tests where parity is required.
- Cover normal, error, replay, and same-thread reuse paths.
- Confirm context cleanup on success, exception, and async completion.
