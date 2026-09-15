# Workflow — ddd4j-quarkus Auth Integration

A canonical end-to-end flow for wiring authentication into a Quarkus service.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the line.
- Locate ddd4j-quarkus-auth and the authentication tests.

## Step 2 — Select the mechanism

- Compare JWT, OIDC, Shiro, and Sa-Token against the deployment model.
- Register exactly one primary SubjectProvider via CDI.

## Step 3 — Wire authorization

- Map identities to AuthPrincipal with explicit role/permission rules.
- Apply RolesAllowed and map security exceptions to stable errors.

## Step 4 — Manage request scope

- Bind the Subject at request start; restore context on success, exception, and async completion.
- Confirm behavior holds under native image boundaries.

## Step 5 — Verify

- Run QuarkusTest suites covering anonymous, valid, expired, and insufficient-role paths.
- Produce a report with mechanism choice, registration points, evidence state, and remaining risk.
