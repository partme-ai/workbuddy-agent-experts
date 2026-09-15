# Workflow — ddd4j-cloud Release Validation

A canonical end-to-end flow for validating and publishing the Cloud lines.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combinations for the eight lines.
- Record each checkout's Git SHA and confirm clean worktrees.

## Step 2 — Verify upstream availability

- Confirm the required Boot and ddd4j artifacts exist remotely for each line.
- Classify anything missing as BLOCKED(upstream).

## Step 3 — Build serially

- Build all eight lines serially with their own Maven 3/4 and JDK contracts.
- Run compatibility scripts and verification consumers.

## Step 4 — Publish and recover

- Deploy to the private repository after explicit authorization; require zero exit and complete remote metadata.
- Exercise private repository recovery where the contract requires it.
- Prove remote availability with isolated clean-cache consumption (-U).

## Step 5 — Report

Produce a single report containing:

- Per-line build, publish, metadata, and consumption results.
- Evidence grading per tier and exact SHAs.
- BLOCKED/SKIPPED inventory and remaining risks.
- Redacted errors only — never credentials.
