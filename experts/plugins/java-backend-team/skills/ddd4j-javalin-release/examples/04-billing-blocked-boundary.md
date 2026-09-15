# Example 4 — Billing-blocked CI and the secret-rotation reflex

## Prompt

> CI on all three branches is failing since this morning. Platform thinks the Maven settings token expired — rotate `MAVEN_SETTINGS_XML` and re-run everything. Also we're authorized to publish tonight, so hurry.

## What the skill should do

1. Diagnose before mutating anything: check whether the CI jobs actually started. If the workflow never launched because of an organization billing/spending limit, this is `BLOCKED (infrastructure)` — not an authentication failure, and no token is involved.
2. Refuse the rotation: changing or rotating `MAVEN_SETTINGS_XML` for an infrastructure block is harmful — it invalidates working credentials and masks the real cause.
3. Keep the gates distinct: CI remains `BLOCKED` even if a local publication is authorized as a fallback tonight; a local publish never turns CI green.
4. Route the authorization boundary (publishing without CI green) through `ddd4j-javalin-production-hardening` and report the sanitized infrastructure reason.

## Expected output

```
Diagnosis: jobs never started — Actions blocked by organization spending limit
(run 8830: "The job was not started because your account has reached a spending limit").
This is BLOCKED (infrastructure), not FAIL (code/credentials).

Actions NOT taken (and why):
  - Rotating MAVEN_SETTINGS_XML: refused — the credential was never exercised;
    rotation invalidates a working secret and hides the root cause.
  - Changing billing/retry settings: out of scope; report and let the owner fix it.

Options: wait for the limit reset (CI stays BLOCKED until terminal runs exist),
or an explicitly authorized local fallback publication — which still leaves
CI BLOCKED, recorded as such in the release report.
```

## Failure the skill must avoid

Rotating the settings secret "to be safe" and re-running. The billing block guarantees the new secret is never even read, three working credentials are now stale, and the real blocker is still in place tomorrow.
