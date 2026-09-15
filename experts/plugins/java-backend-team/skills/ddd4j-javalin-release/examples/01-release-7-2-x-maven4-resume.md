# Example 1 — Full release validation of 7.2.x with Maven 4 resume

## Prompt

> Release `feature/7.2.x` to our private Alibaba Cloud Maven repo. CI already ran. Last attempt died halfway through the upload with a weird 404 — handle that too. We're authorized to publish.

## What the skill should do

1. Record the line contract (7.2.x → Javalin 7.2/ddd4j 3/JDK 21/Maven 4), the exact SHA, and a clean worktree before building.
2. Re-run the clean build plus Security stage on the real toolchain; resolve CI for the exact SHA and wait for terminal required-job conclusions.
3. Classify the earlier failed deploy as partial publication — inspect the RFC9457 404 response and `target/resume.properties`, then resume with the repository-supported retry instead of starting blind.
4. Publish serially, capture the complete module inventory and remote metadata, then prove consumption from an isolated empty-cache repository with `-U`.

## Expected output

```
Release report: feature/7.2.x @ SHA abc123

| Gate              | Result                              |
|-------------------|-------------------------------------|
| Clean build       | PASS (JDK 21, Maven 4, 0 failures)  |
| Security          | PASS (no waivers)                   |
| CI (final SHA)    | PASS (required jobs terminal green) |
| Deploy            | PASS after resume (2 modules retried, target/resume.properties consumed) |
| Empty-cache consume | PASS (parent/BOM + runtime artifacts resolved with -U from isolated repo) |

Inventory: 14/14 modules present, metadata build #47, checksums validated.
```

## Failure the skill must avoid

Reporting the release successful because "the deploy command exited 0 after re-running it from scratch" without the empty-cache proof — or treating the earlier 404 as a repository outage and skipping the resume/inventory validation entirely.
