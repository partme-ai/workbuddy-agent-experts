# Workflow — ddd4j Version Selection

A canonical end-to-end flow for choosing a ddd4j compatibility tuple.

## Step 1 — Collect constraints

- Gather the project type (new/upgrade/maintenance), JDK and Maven versions, and target framework versions.
- Ask whether POM 4.0/Maven 3 is mandatory and whether remote SNAPSHOT consumption plus verified CI are required.

## Step 2 — Lock the main line by JDK

- Java 8→1.0.x, Java 17→2.0.x, Java 21→3.0.x.
- Verify the Maven/POM Model boundary (1.x/2.x: Maven 3/POM 4.0; 3.x: Maven 4/POM 4.1).

## Step 3 — Lock the adapter project

- Match the runtime (Spring Boot, Spring Cloud, Javalin, Quarkus) to its maintenance line in the compatibility matrix.
- Verify the exact upstream framework version, not the branch name.

## Step 4 — Verify evidence

- Check the branch, root POM, java -version, and ./mvnw -version.
- Query private Maven repository metadata and the final SHA.
- Grade evidence: SOURCE / TEST / CI / PUBLISHED / CONSUMED.

## Step 5 — Report

Produce a single report containing:

- Recommended combination (JDK, Maven, POM, ddd4j, adapter project, framework) and rationale.
- Alternatives, incompatible items, and unverified items.
- Evidence status and follow-up verification commands.
- Missing inputs listed as "missing: specific item; how to provide: path or configuration".
