# Workflow — Changing a ddd4j BOM or Parent

A canonical end-to-end flow for editing ddd4j Maven governance.

## Step 1 — Decide the scope

- Are you adding a new module, bumping a version, or migrating a maintenance line?
- Identify whether the change touches `parent`, `dependencies`, or `BOM`.
- Confirm the maintenance line (1.0.x / 2.0.x / 3.0.x) and its JDK / Maven / Model contract.

## Step 2 — Make the edit

- Edit only the file that owns the change.
- For POM 4.1 / 3.0.x, use `<subprojects>` / `<subproject>`; for older lines, use `<modules>` / `<module>`.
- Never duplicate third-party versions in concrete modules.

## Step 3 — Validate

- Run `scripts/test_maven4_model_contract.py` for 3.0.x.
- Run `scripts/test_dependency_property_layout.py` to confirm property layout.
- Run `scripts/test_bom_import_conflicts.py` to detect import conflicts.
- Run `scripts/test_dependency_alignment.py` and `scripts/check-bom-alignment.sh`.

## Step 4 — Verify consumption

- Generate `help:effective-pom` in a consumer project.
- Run `dependency:go-offline` and `compile` against a clean local Maven repository with `-U`.
- Confirm parent, dependencies, BOM, and at least one representative JAR resolve remotely.

## Step 5 — Report

Produce a single report containing:

- Maintenance line, JDK, Maven, POM Model.
- Files changed and the ownership that was added or removed.
- Effective POM excerpts that demonstrate the resolution.
- Validation script outputs.
- Clean-cache consumption result.
- Evidence status per gate (SOURCE / TEST / CI / PUBLISHED / CONSUMED).
