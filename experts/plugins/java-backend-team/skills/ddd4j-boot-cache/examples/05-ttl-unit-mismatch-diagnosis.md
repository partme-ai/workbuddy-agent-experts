# Example 5 — TTL unit mismatch diagnosis

## Prompt

> We set session-ish cache entries to expire after 30 units in the config. In production, entries vanish almost immediately and our downstream calls spike. Locally everything looks fine. What's going on?

## What the skill should do

1. Treat "locally fine, production expires instantly" on a freshly wired cache as a TTL-unit mismatch candidate before blaming the backend.
2. Read the line's Properties source and determine the actual unit the configuration binds — the value is 30, but the unit decides whether that means 30 seconds or 30 milliseconds.
3. Reproduce with a timed test against the real backend: write, measure actual time-to-expiry, compare to intent.
4. Fix at the configuration level (explicit unit if the Properties support it, otherwise convert the value) and document the unit at the call site.
5. Re-run expiry plus downstream-behavior checks and report the corrected semantics.

## Expected output

```
Symptom: cache entries evicted ~instantly in production; local runs look fine.

Evidence:
  config value: cache.session-ttl: 30 (unitless in application.yml)
  line Properties binding: Duration-style → unit applied: MILLISECONDS
  intended: 30 seconds

Timed test (real Redis):
  actual time-to-expiry ≈ 30ms               ← reproduces production
  after fix (30s explicit): ≈ 30s            PASS

Fix: express TTL with an explicit unit in configuration and document the
binding at the call site.

Evidence: SOURCE (Properties read) + timed TEST RUN.
```

## Failure the skill must avoid

Raising the value to "3000" by trial and error until production seems okay. The unit ambiguity stays in place, and the next consumer reading the same key sets 3000 milliseconds intending minutes — the same incident on a delay.
