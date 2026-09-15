# Example 5 — Upgrade done as "just bump the parent"

## Prompt

> We moved our parent from the 2.7.x line to the 3.5.x one and now half the modules won't compile, and the ones that do fail tests talking to the database. Wasn't this supposed to be a version swap?

## What the skill should do

1. Diagnose the real failure: 2.7.x→3.5.x crosses the ddd4j 1.0.x→2.0.x main line, which is not a version swap.
2. Walk the layered upgrade order — JDK→Spring Boot→ddd4j→ddd4j-boot→Maven/POM — and check which layer was skipped. JDK 8→17 is the first gate.
3. Verify dependency resolution and API changes per layer before runtime regressions.
4. Order the remaining verification: context, database, cache, MQ, and web regressions, per the upgrade reference.
5. Report each layer's evidence status and what is still unverified.

## Expected output

```
Diagnosis: the upgrade crossed ddd4j main lines (1.0.x → 2.0.x) but only the
parent was moved.

Layer checklist:
  JDK          — 8 → 17 required; <status>
  Spring Boot  — 2.7.18 → 3.5.16; javax → jakarta impact <status>
  ddd4j        — 1.0.x → 2.0.x API re-verification <status>
  ddd4j-boot   — starter/parent alignment <status>
  Maven/POM    — still 3 / 4.0 (unchanged, correct for 3.x)

Next: verify layer by layer, then run context, database, cache, MQ, and web
regressions. Do not batch-fix across layers.

Evidence: SOURCE (parent diff read). Layered builds NOT RUN yet.
```

## Failure the skill must avoid

Prescribing one big-bang fix (for example "regenerate all imports") without the layer order. Each layer can fail for its own reason, and a batch fix destroys the ability to tell which layer broke.
