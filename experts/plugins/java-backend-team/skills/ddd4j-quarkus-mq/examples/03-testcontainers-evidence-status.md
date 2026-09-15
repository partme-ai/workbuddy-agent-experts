# Example 3 — Evidence request: what did the MQ suite actually prove?

## Prompt

> The release checklist says "MQ tests: PASS", but our CI runner has no Docker this week. What did those MQ tests actually verify, and what's still unknown?

## What the skill should do

1. Separate the evidence tiers: which MQ suites ran without Docker, which needed Testcontainers and were skipped, and how the skips were recorded.
2. State what a no-Docker run can prove (listener wiring, serialization, config keys) and what it cannot (real broker round-trip, ack/nack, recovery).
3. Check how the Docker-dependent suites were recorded — BLOCKED/SKIPPED is honest; PASS without Docker is a false green.
4. List the missing evidence concretely: Testcontainers round-trips for publish/consume, headers, ack/nack/retry, duplicates, recovery.
5. Give the closure path: run the Testcontainers tier on a Docker-capable runner against the release SHA.

## Expected output

```
MQ evidence — release SHA, no-Docker CI week:

  Listener wiring + serialization suites: PASS (no broker needed).
  Testcontainers round-trips (publish/consume, ack/nack/retry, duplicates,
  recovery): BLOCKED — Docker unavailable. Recorded as SKIPPED, NOT PASS.

Unknown until the Testcontainers tier runs: real ack semantics, redelivery
handling, recovery after broker restart.

Checklist correction: "MQ tests: PASS" should read
"MQ tests: PARTIAL — round-trips BLOCKED (no Docker)".
Closure: run Testcontainers tier on a Docker runner for this SHA.
```

## Failure the skill must avoid

Letting "MQ tests: PASS" stand. A skipped real-broker tier is an open risk on a release claiming messaging readiness — SKIPPED must never be folded into PASS.
