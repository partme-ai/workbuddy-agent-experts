# Example 3 — Proving extensions consume the declared upstream artifacts

## Prompt

> Audit whether our extensions really consume the Boot and ddd4j artifacts at the versions the line declares — I suspect one module ships its own copy.

## What the skill should do

1. Fix the combination and branch, then enumerate every extension's upstream dependencies.
2. For each extension, compare declared versus effectively resolved Boot/ddd4j artifact versions (effective POM / dependency tree).
3. Flag any extension that re-pins a managed version as a BOM-ownership violation (route the fix to `ddd4j-cloud-bom`).
4. Run the compatibility tests and verification consumers that exercise those dependencies.
5. Report per-extension evidence: which upstream behaviors were proven and which remain NOT VERIFIED.

## Expected output

```
Extension inventory and upstream versions:
  <ext-1>: Boot <v>, ddd4j <v> — resolved = declared — OK
  <ext-2>: re-pins ddd4j <v'> ≠ BOM <v> — VIOLATION (hand off to ddd4j-cloud-bom)

Behavior evidence:
  compatibility-tests: PASS (line pairing)
  verification consumers: <PASS | NOT RUN>
  remaining gaps: <listed explicitly>

Verdict: <boundary intact | boundary violated — see ext-2>
```

## Failure the skill must avoid

Accepting the POM declarations as proof. A module can declare the BOM-managed version in its own POM while its dependency graph resolves a different, self-shipped copy — only the effective resolution plus runtime verification shows that.
