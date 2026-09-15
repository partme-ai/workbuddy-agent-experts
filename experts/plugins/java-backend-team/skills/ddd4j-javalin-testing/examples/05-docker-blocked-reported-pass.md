# Example 5 — PASS reported while Docker was down

## Prompt

> The release dashboard says our 7.1.x integration suite passed last night. The CI runner had no Docker daemon all night — maintenance window. How is a "PASS" possible, and what do we tell the release manager?

## What the skill should do

1. Diagnose the evidence violation: with no Docker daemon, every Testcontainers-based test either errored (→ FAIL) or was skipped — a PASS claim means skips were translated into green, or the suite silently fell back to in-memory substitutes.
2. Inspect the CI job log and suite config on the current line: find where container tests get conditionally skipped and how the aggregate result is computed.
3. State the correct reporting: container-tier tests are `BLOCKED` (infrastructure), the release gate that depends on them is NOT satisfied, and in-memory fallbacks may not be substituted for container round-trips.
4. Provide the correction contract: the suite must fail (or report BLOCKED) when Docker is absent and container tests were required — never compute a green aggregate from skips.

## Expected output

```
Claim check: "integration suite PASS" during Docker outage.

Log evidence (CI job 8841, 7.1.x):
  - 34 Testcontainers tests: skipped (DockerClientProviderStrategy unavailable)
  - Aggregate result: SUCCESS .............. ← violation: skips counted as pass
  - 0 container-tier assertions executed

Correct status:
  - Container tier: BLOCKED (infrastructure — no Docker on runner)
  - Release gate depending on it: NOT satisfied
  - In-memory substitute used: none found (good), but none may be introduced either.

Fix: suite fails with explicit BLOCKED inventory when required containers cannot
start; dashboard renders BLOCKED, not green. Re-run after runner restore.
```

## Failure the skill must avoid

Telling the release manager "CI was green, so the containers must have run anyway". The PASS was manufactured from 34 skips — the exact skip-to-green translation this skill's evidence rules exist to make impossible.
