# Workflow — ddd4j-javalin Auth Integration

A canonical end-to-end flow for wiring authentication into Javalin routes.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the line.
- Locate the auth module, SubjectProvider implementations, and Keycloak tests.

## Step 2 — Select the framework

- Compare Sa-Token, Shiro, and OIDC/Keycloak against the deployment model.
- Pick exactly one primary SubjectProvider per service.

## Step 3 — Wire route protection

- Apply route-level protection with explicit 401/403 semantics.
- Map the framework identity to AuthPrincipal with explicit role/permission rules.

## Step 4 — Clean up per request

- Bind the Subject at request start; restore context on success, exception, and async completion.
- Confirm no token or cookie leaks into logs.

## Step 5 — Verify

- Test anonymous, valid, expired, insufficient-role, and logout paths with real HTTP requests.
- Produce a report with framework choice, registration points, evidence state, and remaining risk.
