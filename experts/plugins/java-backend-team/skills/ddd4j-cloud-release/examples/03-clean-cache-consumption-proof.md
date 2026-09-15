# Example 3 — Clean-cache consumption proof for a published line

## Prompt

> A consumer team says our published 2023.0.x artifacts don't resolve for them, but they resolve fine on my machine. Settle it with evidence.

## What the skill should do

1. Name the likely cause first: the release machine's warm local repository masks resolution gaps — proof requires isolated clean-cache consumption.
2. Record the deployed version and its remote metadata completeness for 2023.0.x.
3. Run the consumption proof in an isolated environment with a clean cache and `-U`, resolving the consumer coordinates exactly as a downstream would.
4. If resolution fails, capture the redacted error (no credentials) and classify: incomplete metadata vs BLOCKED(upstream) vs repository-side issue.
5. Report the evidence with the exact SHA and coordinates so both teams see the same facts.

## Expected output

```
Consumer coordinates: <groupId:artifactId:version> (2023.0.x line)
Local machine resolution: PASS — warm cache (not evidence)
Isolated clean-cache resolution (-U): FAIL — artifact <x> missing
  remote sources artifact; binary present.

Root cause: incomplete remote metadata — deploy exited zero but did not
upload the full artifact set.

Fix: re-run the deploy step, verify metadata completeness, repeat
clean-cache proof → PASS.
Evidence: REMOTE (isolated). Errors redacted — no credentials echoed.
```

## Failure the skill must avoid

"Proving" resolution on the release machine where the cache is warm. The consumer team's failure is real; only the isolated clean-cache run reproduces what downstream actually experiences.
