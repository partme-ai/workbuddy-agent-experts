# Example 4 — Plain Quarkus REST service, no ddd4j

## Prompt

> Our gateway team's new service is plain Quarkus — no ddd4j anywhere. Set up its REST endpoints, CORS, and error handling using your web skill.

## What the skill should do

1. Recognize the boundary: this skill builds endpoints around the ddd4j request `Context` and ddd4j command/query contracts; a service with no ddd4j dependency does not use that model.
2. Decline to retrofit ddd4j Context/idempotency plumbing onto a non-ddd4j stack — do not use this skill for the plain-Quarkus service.
3. Route to generic Quarkus REST/Java guidance for endpoints, CORS, and error mapping.
4. State the re-engagement condition: once the service adopts `io.ddd4j:ddd4j-quarkus-*` web artifacts, this skill applies (after line selection).
5. If the team actually meant a Spring Boot gateway, route to `ddd4j-cloud-web` / `ddd4j-boot-web` accordingly.

## Expected output

```
Boundary: the ddd4j Context/CAS endpoint model presumes ddd4j-quarkus web artifacts,
which this service does not consume. Retrofitting them is out of scope.

Handoff: generic Quarkus REST guidance covers endpoints, CORS, and error mapping
for the plain service.

Re-engage when: io.ddd4j:ddd4j-quarkus-web appears in the POM — then run
ddd4j-quarkus-version-selection first, and this skill for the endpoint work.
```

## Failure the skill must avoid

Scaffolding ddd4j Context filters and command dispatch into a service whose POM has no ddd4j dependency — the build fails at the first ddd4j import and the team inherits a framework they never chose.
