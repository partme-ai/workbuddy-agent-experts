# Example 2 — Extension boundary review (read-only)

## Prompt

> Audit how we integrated the extensions. Leadership keeps hearing "everything is optional" — verify it.

## What the skill should do

1. Stay read-only — verify the claim, don't refactor.
2. For each integrated extension (excel, monitor, qrcode, validation on this codebase), check the dependency is optional and guarded by a classpath check.
3. Verify the enabled switch exists and that a disabled extension degrades without breaking core startup.
4. Check that no core module imports an extension class in the reverse direction.
5. Check sandboxing on risky inputs: QLExpress limits, plugin policies; and that license keys never reach logs.

## Expected output

| Extension | Optional dep | Classpath guard | Disable-degrades | Reverse import |
|---|---|---|---|---|
| excel | yes | yes | untested | none |
| monitor | yes | yes | yes | none |
| qrcode | **no — compile scope** | n/a | n/a | none |
| qlexpress rules | yes | yes | yes | none; **no timeout limit found** |

Verdict: "everything is optional" is false — qrcode is a hard dependency, and QLExpress lacks a timeout restriction. Evidence: SOURCE only; no application restart was exercised (`NOT RUN`).

## Failure the skill must avoid

Cosigning "fully optional" from the presence of switches. The compile-scope qrcode dependency and the missing QLExpress timeout are precisely what a boundary audit exists to surface.
