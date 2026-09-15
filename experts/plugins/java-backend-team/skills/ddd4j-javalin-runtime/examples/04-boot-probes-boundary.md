# Example 4 — Kubernetes probes for a Spring Boot variant

## Prompt

> We also run this stack under Spring Boot. Wire up the same readiness/liveness logic for K8s probes there, using the same participant registry.

## What the skill should do

1. Decline the direct port: this skill governs the Javalin runtime (`Ddd4jJavalinRuntime`, `JavalinLifecycleParticipant`); the Boot runtime composes participants through Spring auto-configuration with different ownership.
2. Hand off to the Boot skill for the Boot-side wiring.
3. Note what transfers conceptually (readiness aggregates dependencies, liveness stays process-only) so the handoff is actionable.
4. Offer to keep the Javalin side as the behavioral reference the Boot implementation must match.

## Expected output

```
Boundary: participant registry and probe wiring differ per runtime.
For the Spring Boot variant, use ddd4j-boot-autoconfiguration.
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-boot-autoconfiguration

What carries over as a contract (not code):
  - Readiness = aggregated required/optional participants (DB, MQ, OIDC, Outbox)
  - Liveness = process-only, never a dependency check
  - Same reverse-order shutdown semantics

This skill remains the reference for the Javalin lines (6.7.x/7.1.x/7.2.x).
```

## Failure the skill must avoid

Copying the Javalin participant registry into a Spring Boot `@Configuration` because "the runtime is the same concept". Boot has its own lifecycle ownership, and a mechanical port produces two shutdown orders in one process.
