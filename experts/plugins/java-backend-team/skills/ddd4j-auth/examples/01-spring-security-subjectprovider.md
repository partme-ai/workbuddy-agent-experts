# Example 1 — Spring Security behind a SubjectProvider

## Prompt

> New ddd4j 2.0.x project on Spring Boot 3.4. The team knows Spring Security. How do we wire it so our domain services don't import Spring Security types?

## What the skill should do

1. Confirm the runtime/maintenance line before quoting any API.
2. Recommend Spring Security given the team's experience and enterprise requirements (OAuth2/OIDC, method security).
3. Show the unified chain: Spring Security authenticates → `SubjectProvider` maps the identity to `AuthPrincipal` → ddd4j `Subject` → request `Context` → application/domain services.
4. Enforce the boundary: domain reads only `Subject` / `SubjectKit`; `SecurityContext` stays inside the adapter.
5. List the lifecycle and test obligations: bind at entry, restore in `finally`, and cover anonymous/expired/insufficient-role/thread-reuse/logout paths.

## Expected output

A wiring outline: a `SpringSecuritySubjectProvider` implementing ddd4j's `SubjectProvider`, registered by the runtime module, mapping `Authentication` → `AuthPrincipal(profile, roles, permissions)`.

Plus the boundary statement: zero `org.springframework.security.*` imports allowed in the domain module, verified by an import audit.

Plus the test matrix: anonymous → 401-class error, valid → Subject bound, expired → stable error, thread reuse after completion → previous Subject gone. Evidence tier: SOURCE plan only; behavior tests NOT RUN.

## Failure the skill must avoid

Injecting `SecurityContextHolder` reads into domain services "because it's easier." That couples every domain test to Spring Security and leaks identity on pooled threads when cleanup is partial.
