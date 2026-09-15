# Workflow — ddd4j-cloud Version Selection

A canonical end-to-end flow for choosing a ddd4j-cloud combination.

## Step 1 — Collect constraints

- Gather the Spring Cloud line, Boot parent, JDK, Maven, and POM model from the project.
- Record the branch and root POM state.

## Step 2 — Match the primary combination

- Read the eight-line matrix (Hoxton.x through 2025.1.x) mapping Cloud→Boot→ddd4j.
- Confirm the pairing from POMs and verify_cloud_release_matrix.py, not the branch name.

## Step 3 — Verify naming and dependencies

- Confirm the extensions canonical naming; flag any old cmpt references.
- Enumerate upstream (Boot/ddd4j) and downstream (external services) dependencies.

## Step 4 — Verify evidence

- Build and test the selected combination.
- Check CI for the final SHA and consume from the private repository with a clean cache.

## Step 5 — Report

Produce a single report containing:

- Selected primary combination with rationale, plus compatible alternatives.
- Verification commands and evidence state per tier.
- Incompatible, unverified, and upstream-blocked items (BLOCKED(upstream)/BLOCKED(infrastructure)).
- Missing inputs listed as "missing: specific item; how to provide: path or configuration".
