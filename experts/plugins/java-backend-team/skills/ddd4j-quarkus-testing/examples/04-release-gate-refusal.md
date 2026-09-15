# Example 4 — Release-gate request to the testing skill

## Prompt

> All tests are green. Go ahead and mark the release ready, deploy the artifacts to the private repo, and check the CI dashboard for me. Same skill, right?

## What the skill should do

1. Refuse the scope expansion: CI gating, publishing, and remote consumption belong to `ddd4j-quarkus-release`, which requires explicit authorization for any publish.
2. Clarify what "tests green" can and cannot support: behavior evidence at this SHA — not publish readiness, not remote consumability.
3. Point out the two gates the release skill would run that testing does not: CI terminal success for the final SHA and clean-cache (`-U`) consumption proving remote availability.
4. Hand off with the install pattern and the inputs the release skill needs (SHAs, authorization).
5. Do not use the testing skill to mutate repositories or dashboards.

## Expected output

```
Boundary: test results end this skill's scope. Publishing and CI gating are
ddd4j-quarkus-release concerns — publishing additionally requires explicit
user authorization.

What "tests green" supports: behavior evidence at SHA X (with tiers as reported,
including any BLOCKED).

What it does not support: remote availability (needs clean-cache -U consumption)
and release readiness (needs CI terminal success on the final SHA).

Handoff: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-quarkus-release
```

## Failure the skill must avoid

Marking the release ready on test results alone — skipping the CI-on-final-SHA gate and clean-cache consumption. Warm-cache "success" would mask an artifact that was never published.
