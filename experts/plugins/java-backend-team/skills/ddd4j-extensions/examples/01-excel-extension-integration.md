# Example 1 — Integrating the Excel extension

## Prompt

> Our 3.0.x service needs Excel import/export for reports. I saw an `extension-excel` module somewhere — how do we wire it in without coupling the whole app to it?

## What the skill should do

1. Confirm on the current root POM that `extension-excel` exists on 3.0.x — never from a historical module list.
2. Add the dependency as optional with a classpath guard so applications without Excel keep booting.
3. Wire the enabled switch, default implementation, and user Bean override through the runtime / Boot auto-configuration.
4. Name the resource owners (workbook pools, temp files) and make close explicit.
5. Specify the tests: normal export, disabled switch, missing classpath, and shutdown.

## Expected output

```
Integration plan:
  - dependency: extension-excel, scope optional (absent jar must not break core)
  - guard: classpath check + excel.enabled switch in auto-configuration
  - override: user Bean replaces the default ExcelOperations
  - lifecycle: workbook/temp-file owners named; close() idempotent

Tests: export PASS, disabled → feature off and app healthy (planned),
classpath-missing → boots without the capability (planned).
Evidence: SOURCE (module confirmed on 3.0.x root POM); behavior NOT RUN.
```

## Failure the skill must avoid

Declaring the dependency `compile`-required "because the feature needs it." The first consumer that doesn't want Excel then fails at boot — the exact core-pollution the extension boundary exists to prevent.
