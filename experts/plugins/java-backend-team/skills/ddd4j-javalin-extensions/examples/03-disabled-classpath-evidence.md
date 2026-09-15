# Example 3 — Proving the disabled-classpath path

## Prompt

> Our extension is documented as "optional — service runs fine without it". Before we publish that claim, give me evidence the service actually starts and behaves with the extension jar removed.

## What the skill should do

1. Fix the line and locate the composition entry point plus the extension's conditional wiring (how absence on the classpath is detected).
2. Design the evidence run: build/start the service without the extension jar, verify startup succeeds with default wiring, and exercise the affected entry points through the default implementation.
3. Run the paired case: with the extension present, the same entry points must serve the extension behavior — proving the conditional actually switches, not that both states silently serve defaults.
4. Report both runs with evidence states; if the composition tests skip when the jar is absent, that must surface as SKIPPED, not as proof.

## Expected output

```
Claim: extension optional — service runs without it.

Evidence (7.2.x, SHA abc123):
  Run A (extension jar absent):
    - startup ................................ PASS (no ClassNotFound, no bean errors)
    - GET /api/pricing ....................... default pricing served   PASS
    - close/drain ............................ clean, idempotent        PASS
  Run B (extension jar present):
    - GET /api/pricing ....................... extension pricing served PASS
  Conditional wiring: ServiceLoader-based (ExtensionBootstrap.java:41) — verified.

Verdict: claim SUPPORTED for /api/pricing.
Gap: Run A via CI automation NOT RUN (executed manually); scheduled-test gap noted.
```

## Failure the skill must avoid

Supporting the claim because "it's registered as optional in the config". The claim is about a classpath without the jar — a state the build never ran until now, and conditional wiring that has never executed both branches is unproven either way.
