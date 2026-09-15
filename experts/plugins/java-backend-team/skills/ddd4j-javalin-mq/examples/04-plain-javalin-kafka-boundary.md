# Example 4 — Kafka consumer in a plain Javalin app

## Prompt

> Separate project, not on ddd4j: a plain Javalin service that consumes Kafka. Same team, same patterns — just tell us how to register the consumer in the Javalin lifecycle like you do elsewhere.

## What the skill should do

1. Recognize the boundary: without ddd4j there is no `MQClient`, no `JavalinLifecycleParticipant`, and no required/optional readiness contract — this skill's contracts do not exist in that project.
2. Decline to retrofit ddd4j types onto a non-ddd4j codebase, and hand the generic question (Javalin server lifecycle plus Kafka client lifecycle) to `java-skills`.
3. State what conceptually transfers so the handoff is useful: start consumers after the server is up, close them before the server stops, and bound retries with a dead-letter destination.
4. Record the routing decision explicitly.

## Expected output

```
Boundary: this skill's contracts (MQClient, lifecycle participants,
required/optional readiness) are ddd4j-specific and do not exist in a
plain Javalin project — do not retrofit them.

Use java-skills for generic Javalin + Kafka client lifecycle guidance.

Concepts that transfer regardless of framework:
  - Start consumers after the HTTP server accepts; close them before it stops.
  - Ack after successful processing; bound retries with a dead-letter path.
  - Idempotent consumption by message key via a shared store when scaled out.
```

## Failure the skill must avoid

Inventing a `MQClient`-lookalike wrapper for the non-ddd4j project "to keep the patterns consistent". The project has no ddd4j runtime to register it with, so the wrapper would be dead structure — exactly the retrofit this skill must not perform.
