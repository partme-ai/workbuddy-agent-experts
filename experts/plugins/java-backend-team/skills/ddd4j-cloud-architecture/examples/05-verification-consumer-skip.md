# Example 5 — Verification consumer silently skipped in CI

## Prompt

> Our compatibility tests pass on every CI run, but the verification consumers never execute. The dashboard is green — can we trust it?

## What the skill should do

1. Treat a green dashboard with non-executing verification consumers as a false green, not as success.
2. Find why the consumers are skipped: build ordering, module not wired into the reactor, or CI configuration excluding them.
3. Classify correctly: CI that never started the consumers is BLOCKED(infrastructure); a consumer that cannot build for lack of a Boot/ddd4j artifact is BLOCKED(upstream).
4. Re-read the module map to check nothing else drifted while the consumers were dark (naming, upstream versions).
5. Re-run the consumers and grade the evidence honestly before the architecture is called validated.

## Expected output

```
Finding: verification consumers excluded from the CI pipeline —
dashboard green from compatibility tests only.

Classification: BLOCKED(infrastructure) — consumers exist but CI never
invoked them (pipeline stage missing).

Impact: README-listed capabilities lack behavior evidence; the architecture
review cannot mark them verified.

Fix: wire the verification stage into CI for the exact SHA, then re-run.
Evidence: SOURCE + partial TEST; consumers NOT RUN.
```

## Failure the skill must avoid

Reading the green compatibility column as "architecture verified". The skill's core rule is that configuration or pipeline presence is not behavior evidence — skipped consumers must surface as BLOCKED(infrastructure), never silently convert into a pass.
