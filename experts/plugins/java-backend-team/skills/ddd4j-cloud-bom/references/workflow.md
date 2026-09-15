# Workflow — ddd4j-cloud BOM Review

A canonical end-to-end flow for auditing ddd4j-cloud dependency management.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combination.
- Read cloud-parent, cloud-dependencies, and cloud-bom POMs.

## Step 2 — Verify version ownership

- Confirm Spring Cloud and Spring Cloud Alibaba versions come from their own BOMs.
- Confirm Boot parent alignment matches the combination matrix.
- Check that extensions do not re-pin managed versions.

## Step 3 — Verify import order

- Build the effective POM and confirm BOM import order resolves as intended.
- Record consumer coordinates for downstream verification.

## Step 4 — Validate the build

- Run the target module build and tests on the selected combination.
- Check CI for the final SHA.

## Step 5 — Report

Produce a single report containing:

- Combination and effective POM findings.
- Version ownership map and import order confirmation.
- Consumer coordinates and evidence state per tier.
- Violations and risks with proposed fixes.
