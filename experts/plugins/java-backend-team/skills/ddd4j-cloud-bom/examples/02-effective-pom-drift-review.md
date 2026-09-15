# Example 2 — Effective POM drift review

## Prompt

> Two of our services are supposedly on the same ddd4j-cloud line but they resolve different versions of some shared libraries. Read-only check, please.

## What the skill should do

1. Stay read-only — audit, don't fix.
2. Confirm both services target the same Cloud→Boot→ddd4j combination before comparing resolutions.
3. Build the effective POM for each service and diff the resolved versions of the managed libraries.
4. Look for the two classic causes: different BOM import order, or a local `dependencyManagement` entry (or an extension) re-pinning a managed version.
5. Report each drift with the owning POM path, the offending entry, and the corrected import/ownership statement.

## Expected output

| Service | Import order | Re-pins found | Resolved drift |
|---|---|---|---|
| service-a | cloud → alibaba → ddd4j | none | — |
| service-b | alibaba → cloud → ddd4j | `spring-cloud-alibaba` pinned in POM | <library>: vX vs vY |

Verdict: same line, different effective resolution — service-b violates import order and re-pins ownership. Evidence: SOURCE + effective POM read; no runtime test executed.

## Failure the skill must avoid

Concluding "the line is inconsistent" and recommending a version bump. Both services point at the same line; the defect is local import order and re-pinning, which only the effective-POM diff reveals.
