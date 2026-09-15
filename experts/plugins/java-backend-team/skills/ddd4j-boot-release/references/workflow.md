# Workflow — ddd4j-boot Release Validation

A canonical end-to-end flow for validating and publishing ddd4j-boot lines.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the target lines.
- Record the Git SHA of each checkout and confirm a clean worktree.

## Step 2 — Build

- Run a clean build per line with its required JDK and Maven (13 lines total when validating all).
- Run the Security stage; mark exemptions SKIPPED as a risk.

## Step 3 — Gate on CI

- Confirm required CI jobs reached terminal success for the final SHA.
- Mark non-started CI BLOCKED — never PASS.

## Step 4 — Publish and consume

- Deploy to the private repository; confirm deploy exited zero and remote metadata is complete.
- Consume from an isolated clean Maven cache (-U) to prove remote availability.

## Step 5 — Report

Produce a single report containing:

- Per-line build, CI, Security, publish, and consumption results.
- Evidence grading (SOURCE/TEST/CI/PUBLISHED/CONSUMED) per line.
- BLOCKED/SKIPPED inventory and remaining risks.
- Redacted errors only — never credentials or tokens.
