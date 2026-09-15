# Workflow — ddd4j-quarkus Release Validation

A canonical end-to-end flow for validating and publishing the Quarkus lines.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the lines (3.3.x/4.0.x).
- Record each checkout's Git SHA and confirm clean worktrees.

## Step 2 — Build

- Run a clean build per line with Maven 3 (3.3.x) or Maven 4 (4.0.x) and the matching JDK.
- Verify the complete 61-module inventory per deploy.

## Step 3 — Gate on CI and Security

- Confirm required CI jobs reached terminal success for the final SHA.
- Record Security skips as SKIPPED risks — never PASS.

## Step 4 — Publish and consume

- Deploy to the private repository after explicit authorization; require zero exit and complete module inventory.
- Prove remote availability with isolated clean-cache consumption (-U).

## Step 5 — Report

Produce a single report containing:

- Per-line build, CI, Security, publish, and consumption results.
- Evidence grading per tier and exact SHAs.
- BLOCKED/SKIPPED inventory and remaining risks.
- Redacted errors only — never credentials.
