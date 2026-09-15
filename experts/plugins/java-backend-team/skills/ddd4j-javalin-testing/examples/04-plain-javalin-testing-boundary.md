# Example 4 — Testing a plain Javalin app without ddd4j

## Prompt

> Internal tool, plain Javalin, no ddd4j — just JUnit 5 and a HTTP client. Can you set up the same Testcontainers + contract-test conventions you use for the framework services?

## What the skill should do

1. Recognize the boundary: the ddd4j testkits (`web-testkit`, `ddd4j-javalin-testcontainers`) and the lifecycle contracts do not exist in a plain Javalin project, so this skill's machinery cannot be applied there.
2. Decline to retrofit and route the generic question to `java-skills` (JUnit conventions, Testcontainers usage, HTTP assertion libraries).
3. State which principles still transfer so the handoff keeps value: assert full responses, bind port 0, report skipped containers as skipped rather than green.
4. Record the routing decision explicitly.

## Expected output

```
Boundary: this skill's contracts (web-testkit, ddd4j-javalin-testcontainers,
lifecycle suites) are ddd4j-specific — do not retrofit them onto a plain
Javalin project. Use java-skills for generic JUnit + Testcontainers guidance.

Principles that transfer regardless of framework:
  - Assert status, payload, and side effects — never a bare 200.
  - Bind port 0; make tests parallel-safe.
  - Docker unavailable ⇒ suite result is SKIPPED/BLOCKED, not green.
```

## Failure the skill must avoid

Adding the ddd4j testcontainer module to a non-ddd4j pom "to reuse the conventions". The project has no ddd4j runtime to test, so the dependency is dead weight and the lifecycle suites it brings cannot run — a retrofit, which is exactly what must not happen.
