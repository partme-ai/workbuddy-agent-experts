# Example 3 — Ownership proof and clean-cache consumption

## Prompt

> We fixed a re-pinned version in one of our extensions. Prove the fix is real end to end before we tell consumers to upgrade.

## What the skill should do

1. Verify no extension in the line re-pins a managed version anymore (effective POM, not declarations).
2. Record the consumer coordinates consumers must use for the corrected BOM.
3. Publish path belongs to `ddd4j-cloud-release` — hand off there with explicit authorization before any deploy.
4. After publication, prove resolution with an isolated clean-cache consumption (`-U`), not the developer's warm local repository.
5. Grade evidence per tier: SOURCE (POM read), BUILD/TEST, remote consumption — and mark what did not run.

## Expected output

```
Ownership audit: 0 re-pins across extensions (effective POM checked)
Consumer coordinates: <groupId:artifactId:version>
Publication: performed by ddd4j-cloud-release after authorization
  → NOT RUN in this audit

Clean-cache consumption: <PASS — resolved <v> from private repository | NOT RUN>
Evidence status: SOURCE + BUILD; remote tier <graded>.
Missing: authorized publication; how to provide: release window + approval.
```

## Failure the skill must avoid

Declaring the fix "verified" because it builds on the machine where the old artifact is still cached. Warm local repositories hide exactly the resolution this fix changes; only isolated clean-cache consumption proves consumers will get the corrected version.
