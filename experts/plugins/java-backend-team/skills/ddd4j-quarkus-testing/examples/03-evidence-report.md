# Example 3 — Evidence request: full verification report

## Prompt

> Give me the test evidence report for the current SHA: what ran, in which mode, what was skipped, and what's still unproven. Don't sugarcoat it.

## What the skill should do

1. Produce the report per tier with the SHA and line (3.3.x or 4.0.x) named up front.
2. List suites with mode (JVM/native), toolchain, and result — pass, fail, BLOCKED, SKIPPED.
3. Keep tiers separate: source, behavior, container, CI — and never let one imply another.
4. Map results against the feature matrix and name the gaps explicitly.
5. Close with risks and the missing inputs phrased as `missing: item; how to provide: path or configuration`.

## Expected output

```
Test evidence — SHA 9f3c2e1, line 3.3.x (JDK 17, Maven 3, Platform 3.37.4)

JVM mode:
  auth suite          PASS
  web HTTP suite      PASS
  cache TTL suite     PASS
  data (H2) suite     PASS (logic-only evidence)
Containers:
  data (Testcontainers Postgres)  BLOCKED — no Docker
  MQ   (Testcontainers Kafka)     SKIPPED — no Docker
Native:
  native suite        NOT RUN — no GraalVM on runner

Gaps vs feature matrix: real-database behavior, broker round-trips, native path.
Risks: release claim "data + MQ verified" is unsupported at this SHA.
Missing: Docker + GraalVM runner for this SHA; how to provide: CI runner labels.
```

## Failure the skill must avoid

Rolling the tiers up into "14/14 suites passing". The one-line summary hides that the two hardest tiers (containers, native) never ran — which is exactly the decision the report exists to inform.
