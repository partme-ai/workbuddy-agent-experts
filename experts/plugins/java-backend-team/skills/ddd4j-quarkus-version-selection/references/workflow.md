# Workflow — ddd4j-quarkus Version Selection

A canonical end-to-end flow for choosing a ddd4j-quarkus line.

## Step 1 — Collect constraints

- Gather the target Quarkus Platform version, JDK, and Maven from the project.
- Record the branch, root POM model, and wrapper version.

## Step 2 — Match the maintenance line

- 3.3.x→ddd4j 2/JDK17/Maven 3/Quarkus Platform 3.37.4.
- 4.0.x→ddd4j 3/JDK21/Maven 4/Quarkus Platform 3.38.2.
- Confirm the platform version from quarkus-bom.version, never from the line name.

## Step 3 — Verify the toolchain

- Run git branch, java -version, and ./mvnw -version checks.
- Confirm the POM model matches the line contract.

## Step 4 — Verify evidence

- Build and run the line's tests (JVM and, where applicable, native).
- Check CI for the final SHA and consume artifacts from the private repository with a clean cache.

## Step 5 — Report

Produce a single report containing:

- Selected line and complete tuple (Quarkus Platform, ddd4j, JDK, Maven/POM).
- Verification commands and evidence state per tier.
- Incompatible and unverified items.
- Missing inputs listed as "missing: specific item; how to provide: path or configuration".
