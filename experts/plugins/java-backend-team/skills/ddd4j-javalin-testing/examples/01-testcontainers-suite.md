# Example 1 — Testcontainers suite for HTTP + PostgreSQL + Keycloak

## Prompt

> Set up the test suite for our 7.2.x order service: real HTTP contract tests, a real PostgreSQL, and Keycloak for tokens. CI runs multiple suites in parallel, so no port fights please.

## What the skill should do

1. Confirm the line (7.2.x → Javalin 7.2/ddd4j 3/JDK 21/Maven 4) and locate `ddd4j-javalin-testcontainers` plus the web-testkit contract paths.
2. Plan the suite: HTTP contract tests through web-testkit asserting status, payload, and side effects — not just reachability.
3. Wire Testcontainers for PostgreSQL and Keycloak, binding port 0 everywhere so parallel CI suites never collide on fixed ports.
4. Provide the first failing contract test (an endpoint asserting the full response shape) and the container bootstrap order (DB → app → Keycloak before token-issuing tests).

## Expected output

```java
@Container
static PostgreSQLContainer<?> db = new PostgreSQLContainer<>("postgres:16")
        .withCreateContainerCmdModifier(cmd -> cmd.withPortBindings(List.of())); // port 0

@Container
static KeycloakContainer keycloak = new KeycloakContainer(); // realm imported, port 0
```

Plus the suite layout: `*ContractTest` (HTTP via web-testkit), `*RoundTripTest` (containers), and a run report template with per-suite PASS/FAIL/BLOCKED columns.

## Failure the skill must avoid

Hardcoding ports "so debugging is easier" and asserting only that responses are non-empty. The first defect breaks parallel CI; the second produces the 200-smoke false green this skill exists to eliminate.
