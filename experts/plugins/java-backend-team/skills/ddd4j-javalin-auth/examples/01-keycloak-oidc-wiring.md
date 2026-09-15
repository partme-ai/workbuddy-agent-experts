# Example 1 — Wiring OIDC/Keycloak route protection

## Prompt

> Our 7.1.x service needs Keycloak login. Protected routes under `/api`, everything else public. We already run Keycloak in prod. Show me the wiring.

## What the skill should do

1. Confirm the line (7.1.x → Javalin 7.1/ddd4j 2/JDK 17/Maven 3) and read the current OIDC support and `SubjectProvider` contracts in that checkout.
2. Register the OIDC/Keycloak `SubjectProvider` as the single primary provider, with the token validation and issuer/audience config validated at startup.
3. Protect `/api/*` routes explicitly and define 401 (missing/invalid token) versus 403 (valid token, missing role) separately.
4. Map Keycloak realm/client roles to `AuthPrincipal` permissions explicitly, and bind/release the Subject per request on all terminal states.

## Expected output

```java
// one primary SubjectProvider for the service
runtime.register(new KeycloakSubjectProvider(oidcConfig)); // validates at startup

app.beforeMatched("/api/*", ctx -> {
    Subject subject = requireSubject(ctx);        // 401 if missing/invalid token
    requireRole(subject, "order-reader");         // 403 if role absent
});
```

Plus: role mapping table (realm role → `AuthPrincipal` permission), cleanup confirmation for success/exception/async, and evidence state (source read; Keycloak Testcontainers round-trip NOT RUN).

## Failure the skill must avoid

Registering a second `SubjectProvider` "as fallback" alongside the existing Sa-Token one. Two providers resolve by registration order, not policy — the service would silently authenticate through whichever registered first.
