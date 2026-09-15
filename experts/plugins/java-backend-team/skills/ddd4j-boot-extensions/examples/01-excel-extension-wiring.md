# Example 1 — Excel extension wiring

## Prompt

> Our Boot 3 ddd4j service needs Excel export for reports. I saw the extensions module has something for that — wire it in with sensible defaults and a way to turn it off.

## What the skill should do

1. Fix the maintenance line, then list the `ddd4j-boot-extensions` submodules from the root POM and confirm the Excel submodule exists on this line.
2. Add the module and assemble it via its auto-configuration; identify the configuration prefix and default beans from that line's source.
3. Confirm the classpath guard (the underlying Excel library triggers assembly) and the enabled switch's scope.
4. Verify the defaults carry `@ConditionalOnMissingBean` so custom templates or writers can be injected.
5. Prove with the three-state tests: enabled (a real export round-trip), disabled (no beans), and — if feasible — classpath-missing (graceful skip).

## Expected output

```
Selection: Excel extension submodule on line 3.x (confirmed present in
the root POM's extension aggregator).

Wiring:
  - classpath guard: assembles when the underlying library is present
  - off switch: <prefix>.enabled → whole assembly backs off
  - default writer beans guarded by @ConditionalOnMissingBean

Three-state evidence:
  enabled:    real export round-trip PASS
  disabled:   0 extension beans, context green PASS
  library absent: assembly skipped, no startup failure  TEST planned

Evidence: SOURCE + behavior TEST RUN (2 of 3 states). CI: NOT RUN.
```

## Failure the skill must avoid

Wiring the extension "because the module exists" without the enabled switch and guards — the report export then becomes a hard startup dependency, and removing the library in a slimmed deployment kills the whole service.
