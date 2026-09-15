# Example 1 — Design the test plan for a data + auth integration

## Prompt

> We added auth plus a Postgres-backed EventStore to our ddd4j-quarkus 4.0.x service. Design the test plan — what runs in JVM mode, what needs containers, what needs native?

## What the skill should do

1. Fix the line (4.0.x → Quarkus Platform 3.38.2 / ddd4j 3.0.x / JDK 21 / Maven 4) and locate the test fixtures in that checkout.
2. Plan the QuarkusTest suites: auth paths (anonymous/valid/expired/insufficient-role), EventStore round-trips, context binding across request paths.
3. Assign Arc validation for the new `SubjectProvider` and repository registrations — build-time discovery must be exercised.
4. Assign Testcontainers Postgres for real EventStore behavior and mark the Docker-unavailable path BLOCKED/SKIPPED up front.
5. Decide the native tier: JWT parsing and entity reflection are on the native risk list, so a native test run is required for release to native targets.

## Expected output

```
Test plan — SHA, line 4.0.x:

JVM (QuarkusTest, no Docker):
  - Arc validation: SubjectProvider + repository discovery (build-time).
  - Auth paths: anonymous / valid / expired / insufficient-role.
  - Context binding: success, exception, async completion.

Containers (Testcontainers Postgres):
  - EventStore append/read/replay; transaction rollback; startup failure.

Native:
  - JWT parse + entity reflection smoke (required for native release target).

Skips: Docker-unavailable → BLOCKED, reported per tier; never PASS.
```

## Failure the skill must avoid

A plan that runs the EventStore suite against H2 "for speed" and calls the data tier covered. Real-backend behavior was the point of the container tier; substituting it silently drops the strongest evidence.
