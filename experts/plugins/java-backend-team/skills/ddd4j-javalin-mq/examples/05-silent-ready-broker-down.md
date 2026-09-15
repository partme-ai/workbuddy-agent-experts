# Example 5 — Silent READY with the analytics broker down

## Prompt

> Dashboards say our service is perfectly healthy, but analytics hasn't received anything for six hours and nobody got paged. The analytics cluster had a maintenance window. Why were we green?

## What the skill should do

1. Diagnose the silent-READY pattern: the analytics consumer is registered without optional-classification semantics, so its connection failure never reaches the readiness aggregate — the endpoint keeps returning READY.
2. Trace the wiring on the current line: find the analytics listener's registration, its reconnect/error handling, and whether any participant reports its state to readiness.
3. Specify the contract-first fix: optional participant down ⇒ readiness reports an explicit DEGRADED status naming the participant; monitoring pages on the degraded status; required participants keep blocking behavior unchanged.
4. Add the tests: optional broker down ⇒ DEGRADED (currently READY); optional broker recovered ⇒ READY; required broker down ⇒ NOT READY.

## Expected output

```
Diagnosis: analytics consumer failure is invisible to readiness.
  - Registration (AnalyticsListener.java:33): plain participant, no optional
    classification, no readiness contribution.
  - Reconnect errors logged only (AnalyticsListener.java:88) — nobody alerts on logs.

Effect: broker maintenance window ⇒ 6h silent consumption loss, READY throughout.

Fix (contract-first):
  1. RED: optional broker down → readiness DEGRADED, body names "analytics".
  2. GREEN: broker restored → READY; required broker down → NOT READY (unchanged).
  3. Page on DEGRADED, not on log scraping.

Evidence: SOURCE read. Contract tests NOT RUN on this checkout.
```

## Failure the skill must avoid

Answering "add a log-based alert on the reconnect errors". Logs are not a readiness contract — the fix is optional-participant degradation in the readiness aggregate, which is what turns a silent loss into a paged, explicit state.
