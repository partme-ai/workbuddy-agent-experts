# Example 4 — "Just add Spring Security"

## Prompt

> Our team knows Spring Security well. Add Spring Security filters on top of the Javalin service for authorization — same codebase, no rewrite.

## What the skill should do

1. Decline the mix-in: Spring Security is a servlet-filter stack that belongs to the Boot runtime; layering it onto the Javalin runtime creates a second authorization authority that ddd4j's `SubjectProvider` contract does not govern.
2. State the concrete failure mode: two authorities mean 401/403 semantics differ depending on which filter chain intercepts first, and the ddd4j Subject cleanup no longer matches the enforcement point.
3. Route the request: if the requirement is really "the team wants the Boot stack", the work belongs to `ddd4j-boot-auth`; if the service stays on Javalin, express the authorization in the Javalin `SubjectProvider`/route-protection model this skill covers.
4. Record the boundary in the output so the decision is explicit.

## Expected output

```
Not supported on the Javalin runtime: Spring Security filters are a second
authorization authority and bypass the ddd4j SubjectProvider contract
(401/403 semantics and per-request cleanup diverge per filter chain).

Routing:
  - Service moves to Spring Boot → ddd4j-boot-auth
    Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-auth
  - Service stays on Javalin (6.7.x/7.1.x/7.2.x) → define the authorization
    in the SubjectProvider + route protection model (this skill).
```

## Failure the skill must avoid

Instructing the user to register Spring Security's `FilterChainProxy` inside the Javalin embedded server. It can be made to "run", but it produces two authorization authorities in one process — exactly the silent split-brain this skill must prevent.
