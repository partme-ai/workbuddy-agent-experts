# Example 1 — Full 13-line release validation

## Prompt

> Release time for ddd4j-boot. Walk the whole validation: clean builds on every line, CI, security, private repo deploy, and prove the artifacts actually resolve for consumers.

## What the skill should do

1. Fix the target lines via version selection, then record each checkout's Git SHA and confirm clean worktrees.
2. Run the per-line clean build with each line's own JDK and Maven (13 lines), then the Security stage.
3. Gate on CI: terminal success for the final SHA on every line; anything non-started is BLOCKED.
4. Deploy to the private repository, verify exit code zero and complete remote metadata.
5. Prove consumption from an isolated clean cache (`-U`) per line, then assemble the per-line evidence report.

## Expected output

```
Release validation (13 lines, SHA <sha>, clean worktrees):

  build      13/13 lines PASS (each on its own JDK/Maven)
  security   12 PASS / 1 SKIPPED exemption (carried as risk)
  CI         13/13 terminal success for SHA <sha>
  deploy     exit 0, remote metadata complete
  consume    13/13 resolve from isolated clean cache (-U)

Grading: all lines CONSUMED. SKIPPED inventory: 1 security exemption
(owner, reason, expiry recorded).
```

## Failure the skill must avoid

Declaring the release done after builds and CI. The 1.0.x lines could build perfectly while never having been published — only the clean-cache consumption step separates a real release from a local illusion.
