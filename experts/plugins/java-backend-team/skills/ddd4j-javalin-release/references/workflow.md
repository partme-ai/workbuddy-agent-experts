# Workflow — ddd4j-javalin Release Validation

A canonical end-to-end flow for validating and publishing the Javalin lines.

## Step 1 — Confirm the source of truth

- Run ddd4j-javalin-version-selection to fix the lines (feature/6.7.x, feature/7.1.x, feature/7.2.x).
- Record each checkout's Git SHA and confirm clean worktrees.

## Step 2 — Build

- Run a clean build per line with its own JDK/Maven/POM contract.
- Run the Security stage; record waivers as SKIPPED risks.

## Step 3 — Gate on CI

- Confirm required Actions jobs reached terminal success for the final SHA.
- Mark billing-blocked CI as BLOCKED — never PASS.

## Step 4 — Publish and consume

- Deploy serially to the private Maven repository after explicit authorization.
- Prove remote availability with isolated clean-cache consumption (-U); verify Maven 4 resume state via target/resume.properties when applicable.

## Step 5 — Report

Produce a single report containing:

- Per-line build, CI, Security, publish, and consumption results.
- Evidence grading per tier and exact SHAs.
- BLOCKED/SKIPPED inventory and remaining risks.
- Redacted errors only — never credentials.
