# Example 2 — Extensions wiring review (read-only)

## Prompt

> We ship with every extension module enabled by habit. Read-only audit: which ones are actually used, which are dead weight, and is anything unsafe to keep?

## What the skill should do

1. Stay read-only; findings with severity, not patches.
2. Fix the line, then list the extension submodules on that line and cross-check against what the application actually uses.
3. For each assembled extension, read its guards and switch scope — flag any whose disable path leaves beans behind.
4. Flag security-relevant extensions (QLExpress-style script execution) assembled without corresponding control needs.
5. Verify resource lifecycle per extension (owners, idempotent close) and what evidence exists per state.

## Expected output

| Extension | Status | Finding | Severity |
|---|---|---|---|
| Excel | used | guards + off switch verified | OK |
| QRCode | used | default beans overridable; tests exist for enabled only | Low |
| Akka | dead weight | assembled, zero call sites; adds actor threads at startup | Medium |
| QLExpress | unused but enabled | script engine assembled; disable leaves the evaluator bean alive | High |
| Monitor | used | no disabled-state test | Unverified |

Recommendation: drop Akka and QLExpress from the deployment; QLExpress first (script surface with no caller).

Evidence: SOURCE read on line <L>. Three-state tests NOT RUN — read-only review.

## Failure the skill must avoid

Auditing by POM contents only. The dangerous finding — a script engine assembled with no caller and a half-working off switch — is invisible without reading the wiring and the application's actual call sites.
