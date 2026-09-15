# Example 1 — Validating and publishing one line

## Prompt

> Our extensions changes are merged on 2025.0.x. Validate the line and publish it to our private repository — we're authorized for the deploy.

## What the skill should do

1. Fix the combination with `ddd4j-cloud-version-selection`, record the checkout SHA, and confirm a clean worktree.
2. Verify the upstream Boot/ddd4j artifacts for 2025.0.x exist remotely before building.
3. Build the line with its own Maven/JDK contract and run the compatibility scripts and verification consumers.
4. Deploy to the private repository — authorization confirmed here — and require zero exit plus complete remote metadata.
5. Prove consumption with isolated clean-cache `-U` resolution, and report with exact SHAs and per-tier evidence.

## Expected output

```
Line: 2025.0.x — SHA <sha>, worktree clean
Upstream: Boot <v>, ddd4j <v> — present remotely — OK
Build: PASS (Maven <x>, JDK <y>)
Compatibility + verification consumers: PASS
Publish: authorized → zero exit; remote metadata complete
Clean-cache consumption (-U): PASS — all artifacts resolved

Evidence: BUILD + TEST + REMOTE, all tiers graded; BLOCKED/SKIPPED: none.
```

## Failure the skill must avoid

Treating the deploy's zero exit code as done. Without the complete remote-metadata check and the clean-cache consumption proof, consumers can still fail to resolve — the release is not proven until an isolated environment pulls every artifact.
