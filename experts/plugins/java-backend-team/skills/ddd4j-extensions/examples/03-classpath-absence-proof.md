# Example 3 — Proving degradation when the extension jar is absent

## Prompt

> We claim the OTel extension is fully optional. Marketing even put it on the feature list. Show me the evidence that an app built without it still runs clean.

## What the skill should do

1. State the required evidence precisely: a build without the extension jar, a boot, a request served, and a shutdown — all clean, with the feature reported as degraded rather than failed.
2. Check the source for the classpath guard and confirm no core or runtime class imports the extension package unconditionally.
3. Specify the test matrix: with-jar enabled, with-jar disabled, without-jar — each asserting startup, request, and shutdown behavior.
4. Run or request the matrix; grade evidence per case and mark what was not executed.
5. Flag the Noop/degraded reporting requirement: absence must be observable, not silent.

## Expected output

```
Claim: extension-otel is optional.

Static check (SOURCE):
  - extension class referenced only behind ClassUtils.isPresent guard  ← OK
  - runtime auto-configuration conditional on @ConditionalOnClass       ← OK

Runtime matrix:
  - with-jar, enabled    : startup + export chain   → planned
  - with-jar, disabled   : degraded, startup clean  → planned
  - without-jar          : startup + requests clean → planned, NOT RUN

Verdict: source-level optionality CONFIRMED; runtime degradation NOT PROVEN.
Missing: the three-case boot matrix; how to provide: build one app image
without the extension jar and run the smoke suite.
```

## Failure the skill must avoid

Pointing at the `@ConditionalOnClass` annotation as proof. The guard is necessary but not sufficient — an unguarded import deeper in the chain or a startup assertion can still break the without-jar boot, and only running the matrix catches it.
