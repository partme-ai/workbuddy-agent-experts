# Example 1 — JWT authentication on the 4.0.x line

## Prompt

> Our Quarkus service needs JWT auth. We're on ddd4j-quarkus 4.0.x. Wire it so our controllers see the ddd4j Subject and role checks work.

## What the skill should do

1. Fix the line first (4.0.x → Quarkus Platform 3.38.2 / ddd4j 3.0.x / JDK 21 / Maven 4) and read `ddd4j-quarkus-auth` in that checkout.
2. Confirm JWT fits the deployment model (local validation, no external IdP round-trip per request).
3. Register exactly one primary `SubjectProvider` via CDI and map validated token claims to `AuthPrincipal` with explicit role/permission rules.
4. Apply `RolesAllowed` on protected endpoints and map security exceptions to stable 401/403 responses — never raw provider internals.
5. Plan verification: QuarkusTest for anonymous, valid, expired, and insufficient-role paths.

## Expected output

```java
@ApplicationScoped
public class JwtSubjectProvider implements SubjectProvider {
    // resolves Subject from the validated JWT identity, per request
}

// endpoint
@POST @RolesAllowed("order:write")
public Response create(OrderCommand cmd) { ... }
```

Plus the test matrix: anonymous → 401; valid + role → 200; expired → 401;
valid without role → 403; and a request-scope release check for all paths.
Evidence: SOURCE produced, TEST(native) pending where deployment requires native.

## Failure the skill must avoid

Wiring Spring Security-style `SecurityContextHolder` semantics into Quarkus, or registering a second SubjectProvider "for the admin endpoints". Both compile and then fail: the first fails authorization, the second fails the Arc ambiguous-resolution build.
