# Example 2 — Read-only composition review

## Prompt

> We have five extensions wired into our 6.7.x service and two teams keep reporting "my binding didn't apply". Read-only review of the whole composition, please.

## What the skill should do

1. Stay read-only; reconstruct the exact module installation order from the composition entry point with file/line evidence.
2. Check every `Modules.override` call: the overridden default must be installed before the override applies; flag any business module installed before its target.
3. Enumerate SPI registrations per contract and flag duplicate providers — the runtime resolves them nondeterministically, which matches the "sometimes my binding applies" symptom.
4. Check lifecycle: each extension's resources have an owner, close is idempotent, and failure semantics are explicit (optional degrades, required fails startup).

## Expected output

```
Composition order (reconstructed):
  1. CoreModules .............. defaults
  2. WebModule, DataModule .... capability defaults
  3. BusinessPricingModule .... ← override target installed here
  4. AuditExtension ........... plain install, no override   ← OK
  5. TenancyModule ............ overrides CoreModules        ← DEFECT

Findings:
  - TenancyModule's Modules.override targets core bindings installed at step 1 —
    valid. But TeamB's ReportingModule (step 3.5) overrides WebModule bindings
    installed at step 2 — currently installed BEFORE... verified OK.
  - SPI `MetricsCollector`: registered by AuditExtension AND ReportingModule
    → duplicate provider, resolution is nondeterministic  ← root cause of
    "my binding didn't apply" reports.
  - ReportingModule resources: no lifecycle owner (leak on restart).

Not verified: no behavior test executed in this review.
```

## Failure the skill must avoid

Answering "check your module order" without reconstructing it. The reports are caused by a duplicate SPI provider — invisible in any single file and provable only by enumerating the full registration set.
