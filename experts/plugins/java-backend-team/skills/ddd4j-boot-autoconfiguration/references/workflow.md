# Workflow — ddd4j-boot Auto-Configuration Review

A canonical end-to-end flow for creating or reviewing a Spring Boot auto-configuration.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line.
- Locate the feature's AutoConfiguration, Properties, and imports metadata.

## Step 2 — Map conditions and defaults

- List ConditionalOnClass/Property/MissingBean conditions and configuration prefixes.
- Identify default beans and user override points.

## Step 3 — Verify wiring

- Confirm the off switch truly skips assembly.
- Confirm destroyMethod, resource owners, failure rollback, and idempotent close.

## Step 4 — Test

- Execute target context tests and behavior tests.
- Cover the user-override path explicitly.

## Step 5 — Report

Produce a single report containing:

- Version line and configuration entry points.
- Default implementations and override points.
- Test results and evidence state (configuration presence, bean creation, behavior, CI, publish reported separately).
- Risks with proposed fixes and missing inputs.
