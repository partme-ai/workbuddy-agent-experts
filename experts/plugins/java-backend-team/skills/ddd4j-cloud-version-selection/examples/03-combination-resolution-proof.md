# Example 3 — Proving the combination actually resolves

## Prompt

> We picked the 2025.0.x combination on paper. Prove it resolves and builds before we migrate the first service.

## What the skill should do

1. Confirm the 2025.0.x branch, SHA, and clean worktree before building anything.
2. Build the selected combination and record the exact Maven/JDK toolchain used.
3. Check CI for the final SHA — if CI never started, mark BLOCKED(infrastructure), do not guess.
4. Prove downstream consumption from the private repository with an isolated clean cache (not a warm local repo).
5. Classify anything missing upstream (Boot/ddd4j artifacts) as BLOCKED(upstream) rather than patching locally.

## Expected output

```
Combination: 2025.0.x primary pairing
Build: PASS (Maven <x>, JDK <y>, SHA <sha>)
CI: <PASS for SHA | BLOCKED(infrastructure) — run never started>
Remote consumption: <PASS with clean cache -U | NOT RUN>
Upstream artifacts: <all present | BLOCKED(upstream): <artifact>>

Verdict: <combination verified | combination blocked>
Evidence: SOURCE + BUILD; CI and remote-consumption tiers <graded>.
```

## Failure the skill must avoid

Reporting "the combination works" from a warm local repository or a successful compile alone. Without CI evidence for the exact SHA and clean-cache remote consumption, the claim is unverified and must be marked as such.
