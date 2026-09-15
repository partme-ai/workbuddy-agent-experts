# Workflow — ddd4j-javalin Version Selection

A canonical end-to-end flow for choosing a ddd4j-javalin maintenance line.

## Step 1 — Collect constraints

- Gather the target Javalin version, JDK, and Maven from the project.
- Record the branch, root POM model, and wrapper version.

## Step 2 — Match the maintenance line

- 6.7.x→Javalin 6.7/ddd4j 1/JDK17/Maven 3.
- 7.1.x→Javalin 7.1/ddd4j 2/JDK17/Maven 3.
- 7.2.x→Javalin 7.2/ddd4j 3/JDK21/Maven 4.
- Verify against BuildLineContractTest and the current POMs, not the branch name alone.

## Step 3 — Verify the toolchain

- Run git branch, java -version, and ./mvnw -version checks.
- Confirm the POM model and modules/subprojects layout match the line contract.

## Step 4 — Verify evidence

- Build and run the line's behavior tests.
- Check CI status for the final SHA; consume artifacts with an isolated clean cache where required.

## Step 5 — Report

Produce a single report containing:

- Selected line and complete tuple (Javalin, ddd4j, JDK, Maven/POM).
- Verification commands and evidence state per tier.
- Incompatible and unverified items.
- Missing inputs listed as "missing: specific item; how to provide: path or configuration".
