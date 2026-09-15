# Example 5 — Directory existence mistaken for a working capability

## Prompt

> I see a `cache` module and a `metrics` package in the repo, so caching and observability are done, right? Management wants it on the release notes.

## What the skill should do

1. Refuse the inference: a module's existence does not mean the capability works — require entry point, registration, and behavior evidence.
2. Check each claimed capability for the three proofs: does an adapter implement the port, does the runtime register it, do behavior tests exercise it?
3. Distinguish what the directory shows (source exists) from what it cannot show (registration, lifecycle, tests passing).
4. Report per-capability evidence status so the release note claim is graded, not binary.

## Expected output

```
Claim: "caching and observability are done"

cache:
  - Adapter implementing Cache SPI: FOUND (CaffeineCache, SOURCE)
  - Runtime registration: FOUND (runtime module binds it, SOURCE)
  - Behavior test (put/get/TTL): FOUND, last run PASS (TEST)
  → supportable claim.

metrics:
  - Adapter: OpenTelemetryProjectionMetrics present (SOURCE)
  - Runtime registration: NOT FOUND — NoopProjectionMetrics still bound
  → claim NOT supportable; observability is degraded, not done.

Evidence: SOURCE + TEST for cache; SOURCE only for metrics.
Missing: metrics registration + export test; how to provide: bind the OTel
implementation and run the export chain test.
```

## Failure the skill must avoid

Signing off "yes, both are done" because the packages exist. The metrics case is exactly the trap: code present, registration absent, dashboards forever empty.
