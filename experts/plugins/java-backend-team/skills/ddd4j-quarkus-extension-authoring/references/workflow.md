# Workflow — ddd4j-quarkus Extension Authoring

A canonical end-to-end flow for authoring a Quarkus extension.

## Step 1 — Confirm the source of truth

- Run ddd4j-quarkus-version-selection to fix the line.
- Locate ddd4j-quarkus-extensions and extension-parent.

## Step 2 — Structure the extension

- Create paired runtime and deployment modules.
- Implement the Processor with explicit BuildItem consumption/production and Recorder calls.

## Step 3 — Register beans and configuration

- Define CDI scopes and configuration mappings in the runtime module.
- Register beans via BuildItems, never assuming a BOM import registers anything.

## Step 4 — Verify native boundaries

- Confirm reflection/serialization registrations needed for native image.
- Confirm Docker detection accounts for Quarkus's multiple classloaders.

## Step 5 — Verify

- Run Arc/QuarkusTest suites plus a native test where the contract requires it.
- Produce a report with extension structure, registration points, evidence state, and remaining risk.
