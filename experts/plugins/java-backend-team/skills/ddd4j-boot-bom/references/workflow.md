# Workflow — ddd4j-boot BOM Review

A canonical end-to-end flow for auditing ddd4j-boot dependency management.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line, JDK, Maven, and POM model.
- Read boot-parent, boot-dependencies, and boot-bom POMs.

## Step 2 — Verify version ownership

- Confirm ordinary third-party versions live in ddd4j-dependencies.
- Confirm the Boot layer only overrides the Boot ecosystem.
- Check that concrete modules do not re-pin managed versions.

## Step 3 — Verify import order

- Build the effective POM (mvn help:effective-pom).
- Confirm Spring Boot BOM and ddd4j BOM imports resolve in the intended order.

## Step 4 — Validate the build

- Run the target module build and tests on the selected line.
- Check CI status for the final SHA.

## Step 5 — Report

Produce a single report containing:

- Version line and effective POM findings.
- Version ownership map (who manages which coordinates).
- BOM import order confirmation.
- Tests and CI evidence, each layer reported separately.
- Violations and risks with proposed fixes.
