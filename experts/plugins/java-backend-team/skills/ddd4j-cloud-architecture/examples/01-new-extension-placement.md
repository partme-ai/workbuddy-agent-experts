# Example 1 — Placing a new extension module

## Prompt

> We want to add a Sentinel rules extension to ddd4j-cloud. Where does it go, what may it depend on, and how do we name it?

## What the skill should do

1. Fix the target combination first with `ddd4j-cloud-version-selection` and confirm the branch and SHA.
2. Place the module inside the `extensions` area using canonical `extensions` naming — no old `cmpt` naming.
3. Declare the upstream boundary: which Boot/ddd4j artifacts the extension consumes, managed by the BOM (no re-pinned versions).
4. Specify the required companions: a compatibility-test entry and a verification consumer for the Sentinel behavior.
5. Mark what remains unproven (real Sentinel connectivity) as NOT VERIFIED until tested.

## Expected output

```
Placement: extensions/<sentinel-extension> (canonical extensions naming)
Upstream deps: <Boot/ddd4j artifacts from the line> — versions owned by the BOM
Companions required:
  - compatibility-tests entry (line pairing)
  - verification consumer proving real Sentinel rule behavior
Naming check: no cmpt references — OK
Open items: Sentinel connectivity NOT VERIFIED (external service).
```

## Failure the skill must avoid

Creating the module as a top-level sibling of `extensions` with its own hard-coded dependency versions. That breaks both the canonical module layout and BOM ownership, and it ships without the compatibility/verification evidence the architecture requires.
