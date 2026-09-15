# Example 1 — Adding a module without leaking versions

## Prompt

> We're adding an `sms` module to the 2.0.x line. It needs a third-party SDK. Where do I declare things so the release checkers don't reject it?

## What the skill should do

1. Confirm the line's contract: 2.0.x means Maven 3 / POM 4.0, so the aggregator keeps `<modules>` / `<module>`.
2. Place each declaration by ownership: build/plugin conventions in `ddd4j-parent`, the SDK version as a property in `ddd4j-dependencies`, and the new ddd4j artifact coordinate in `ddd4j-bom`.
3. Keep the module POM free of numeric versions — reference managed properties only.
4. Run the validation gates: property-layout and dependency-alignment scripts.
5. Verify consumption: effective POM in a consumer, then clean-cache `dependency:go-offline` / `compile`.

## Expected output

```
Placement:
  - Aggregator (2.0.x): <module>sms</module> added — POM 4.0 syntax kept
  - SDK version: property in ddd4j-dependencies only
  - sms artifact: coordinate added to ddd4j-bom for consumers
  - sms/pom.xml: zero numeric versions; managed properties only

Validation:
  - test_dependency_property_layout.py PASS
  - test_dependency_alignment.py PASS

Evidence: SOURCE + TEST gates run. Clean-cache consumption NOT RUN.
Missing: remote resolve; how to provide: run dependency:go-offline with -U
on an empty local repo once the line is published.
```

## Failure the skill must avoid

Handing back a module POM with the SDK version hardcoded "because it's only one place." That pin silently overrides the platform version and reappears as an alignment failure on the next release.
