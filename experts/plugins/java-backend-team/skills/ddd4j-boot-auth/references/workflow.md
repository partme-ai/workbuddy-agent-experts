# Workflow — ddd4j-boot Auth Integration

A canonical end-to-end flow for wiring authentication through ddd4j-boot.

## Step 1 — Confirm the source of truth

- Run ddd4j-boot-version-selection to fix the line.
- Locate the auth AutoConfiguration, Properties, and the corresponding ddd4j-auth modules.

## Step 2 — Select the security framework

- Compare Sa-Token, Shiro, and Spring Security against the account model and existing investment.
- Confirm exactly one primary SubjectProvider is assembled.

## Step 3 — Verify wiring

- Check conditional wiring, default beans, and user Bean override points.
- Confirm the off switch truly skips assembly and exception handling maps to the web error contract.

## Step 4 — Test

- Execute context and behavior tests: anonymous, valid, expired, insufficient-role, logout, and thread reuse.
- Confirm no Subject or token leaks across requests.

## Step 5 — Report

Produce a single report containing:

- Framework and artifacts selected with configuration keys.
- AutoConfiguration entry points and override points.
- Test results and evidence state (configuration, bean, behavior, CI, publish reported separately).
- Risks with proposed fixes and missing inputs.
