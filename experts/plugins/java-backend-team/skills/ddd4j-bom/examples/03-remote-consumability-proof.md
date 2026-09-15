# Example 3 — Proving remote consumability after a release

## Prompt

> Release engineering says the 2.0.x deploy ran green. A teammate in another office says they can't resolve the new `ddd4j-core` SNAPSHOT. Who's right, and how do we settle it?

## What the skill should do

1. Name the two different claims: "the deploy pipeline succeeded" vs "the artifacts are remotely consumable" — green pipeline does not prove the second.
2. Settle it with the clean-cache gate: empty the local repository (or use a temp `maven.repo.local`), then run `dependency:go-offline` and `compile` with `-U` against the remote.
3. Check the specific artifacts: parent, BOM, and at least one representative JAR — a resolvable BOM does not mean every module was uploaded.
4. Record evidence grades: CI for the deploy run, CONSUMED only after the clean-cache resolve succeeds.
5. Point out the warm-cache trap: any machine that resolved these artifacts before masks the gap.

## Expected output

```
Question: is 2.0.x SNAPSHOT remotely consumable?

Test (run on a machine with a cold repo):
  mvn -U -Dmaven.repo.local=/tmp/clean-repo dependency:go-offline
  mvn -Dmaven.repo.local=/tmp/clean-repo compile

Result: parent resolves, ddd4j-bom resolves, ddd4j-core SNAPSHOT
        → 404 NOT FOUND  ← deploy partial

Verdict: teammate is right; the release is NOT consumable end to end.
Evidence: CI (deploy ran) + CONSUMED (failed) — the partial-upload window
is documented, re-run the deploy, then repeat the cold-cache gate.
```

## Failure the skill must avoid

Accepting the green pipeline as proof and telling the teammate to "clear their cache." The warm cache on release machines is precisely what hid the partial upload.
