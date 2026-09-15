# Workflow — ddd4j-boot Version Selection

A canonical end-to-end flow for choosing a ddd4j-boot line.

## Step 1 — Collect constraints

- Gather the Spring Boot version, JDK, and Maven from the current project.
- Record the current parent/BOM and whether the project is new, upgraded, or in maintenance.

## Step 2 — Match the maintenance line

- Read the 13-line matrix (config/consistency/ddd4j-boot-build-matrix.tsv).
- Output the complete Boot→ddd4j→JDK→Maven/POM tuple.

## Step 3 — Verify the toolchain

- Confirm Boot 4 targets use Maven 4/POM 4.1/subprojects.
- Run git branch, java -version, and ./mvnw -version checks.

## Step 4 — Verify evidence

- Build and run tests on the selected line.
- Check CI status for the final SHA.
- Consume the artifact from the private repository with an isolated clean cache (-U).

## Step 5 — Report

Produce a single report containing:

- Selected line and complete tuple, with rationale.
- Incompatible and unverified items.
- Evidence status (SOURCE/TEST/CI/PUBLISHED/CONSUMED).
- Upgrade path steps when the request is an upgrade.
- Missing inputs listed as "missing: specific item; how to provide: path or configuration".
