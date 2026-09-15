# Example 4 — Boundary: refusing to force POM 4.1 onto an old line

## Prompt

> The 1.0.x line is annoying — everyone else is on Maven 4. Just convert the whole line to POM 4.1 with `<subprojects>` so our tooling is uniform, and bump the versions while you're in there.

## What the skill should do

1. Refuse the model flattening: 1.0.x / 2.0.x are contractually Maven 3 / POM 4.0; forcing `<subprojects>` onto them breaks every consumer and CI job pinned to Maven 3.
2. Refuse the silent version bump: changing versions without explicit authorization and a recorded decision is an explicit out-of-scope action.
3. Explain the toolchain contract is per-line by design: 3.0.x is the Maven 4 / POM 4.1 line; uniformity across lines is not a goal.
4. Offer the legitimate path: run the Maven 4 work on 3.0.x, or escalate a real toolchain migration as a deliberate line-level decision with gates.

## Expected output

```
Refusal 1 (model flattening): 1.0.x stays Maven 3 / POM 4.0. The
<modules>/<module> syntax is part of that line's contract; swapping it for
<subprojects> leaves the line unbuildable for every Maven 3 consumer.

Refusal 2 (silent version bump): versions change only with explicit
authorization, validated by the alignment scripts and a clean-cache
consumption gate — not as a side effect of a syntax edit.

Legitimate route: Maven 4 / POM 4.1 work belongs on the 3.0.x line. A
cross-line toolchain migration is a version-selection decision, not a BOM
edit.
```

## Failure the skill must avoid

Producing the "uniform" 4.1 POM for 1.0.x because it was asked for. Toolchain flattening bricks the old line's consumers — the exact anti-pattern this skill exists to block.
