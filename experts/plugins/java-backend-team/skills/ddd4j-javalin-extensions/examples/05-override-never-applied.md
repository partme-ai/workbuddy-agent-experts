# Example 5 — The override that silently never applied

## Prompt

> We shipped our tax-calculation override last sprint. Staging numbers still come from the default calculator, yet our composition unit test passes. Everyone swears the module is installed. Where do we look?

## What the skill should do

1. Suspect the classic composition defect: the override is installed before (or without) the default module it overrides — the unit test passes because it builds its own injector in the correct order, not the production composition.
2. Reconstruct the production composition order on the current line with file/line evidence: where defaults install, where the tax override installs.
3. Check the test itself: if it constructs `Guice.createInjector(defaults, Modules.override(defaults).with(business))` locally instead of calling the production composition method, it tests a different graph.
4. Fix contract-first: a test that calls the real composition entry point and asserts the business `TaxCalculator` binding wins; then verify through the public entry point.

## Expected output

```
Diagnosis: override applied to a different injector than production uses.
  - Production composition (ServiceComposition.java:60): defaults installed,
    tax override installed ONLY when `features.tax=true` — staging config lacks
    the flag ⇒ default TaxCalculator serves.
  - Unit test (TaxOverrideTest.java:18): builds its own injector with the flag
    hardcoded ⇒ passes while production never overrides.

Fix (contract-first):
  1. RED: test must call the real composition method with staging-like config —
     asserts BusinessTaxCalculator serves /api/tax (currently default).
  2. Enable the feature flag in staging profile; assert again.
  3. Add a no-flag test asserting documented default behavior.

Evidence: SOURCE read. Behavior run NOT EXECUTED on this checkout.
```

## Failure the skill must avoid

Adding the flag and re-running the existing unit test to declare victory. The test never exercised the production composition — the fix is meaningless until a test consumes the real composition entry point.
