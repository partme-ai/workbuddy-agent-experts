# Example 3 — BOM import vs real wiring

## Prompt

> Our audit checklist says "cache module integrated". The cache BOM is imported in every service. Is that enough evidence, or do we need more?

## What the skill should do

1. State the core distinction up front: a BOM import pins versions; it does not assemble runtime beans. Build items and recorders do the wiring.
2. Trace the cache extension's deployment module for the BuildItems/Recorder calls that register the actual beans.
3. Verify the runtime module's CDI scopes and configuration mappings exist in the current line.
4. Cross-check that Arc/QuarkusTest suites for the cache module pass on the audited SHA.
5. Return an evidence-status verdict distinguishing SOURCE (wiring exists) from TEST (behavior proven).

## Expected output

```
Question: does "cache BOM imported" prove integration?

Evidence:
  - BOM import present in consumer POMs: YES (SOURCE).
  - cache deployment module registers beans via BuildItems: FOUND (CacheRecorder called from CacheBuildStep, line NN).
  - Arc/QuarkusTest suite for cache module: NOT RUN on audit SHA.

Verdict: BOM import alone is NOT integration evidence.
Wiring exists at SOURCE level; behavior evidence requires the cache module's QuarkusTest run.
Missing: test run on the audit SHA; how to provide: execute the cache module test suite.
```

## Failure the skill must avoid

Accepting the BOM import as proof. Treating a BOM import as a registered bean is the documented anti-pattern — the auditor would green-light services whose cache beans were never assembled.
