# Workflow — ddd4j Authentication Integration

A canonical end-to-end flow for choosing and wiring ddd4j authentication.

## Step 1 — Confirm the source of truth

- Identify the maintenance line, runtime, and POM.
- Confirm which authentication framework the project already uses.

## Step 2 — Select the framework

- Compare Sa-Token, Shiro, and Spring Security against the account model, token requirements, and existing investment.
- Pick exactly one primary SubjectProvider.

## Step 3 — Wire the SubjectProvider

- Map the framework identity (StpLogic, Shiro Subject, or SecurityContextHolder Authentication) to AuthPrincipal.
- Define profile, roles, and permissions with explicit mappings.
- Register the provider in the runtime module.

## Step 4 — Bind and clean up per request

- Bind the Subject at request start.
- Restore the previous context on success, exception, async completion, and thread reuse.

## Step 5 — Map exceptions

- Convert framework exceptions into the stable web error contract.
- Distinguish unauthenticated, insufficient permission, and expired token.

## Step 6 — Verify

- Test anonymous, valid, expired, insufficient-role, logout, and thread-reuse paths.
- Confirm no token or API key appears in logs.

## Report

Produce a single report containing:

- Framework and artifacts selected, with configuration keys.
- SubjectProvider registration points and lifecycle owners.
- Exception mappings.
- Tests run and evidence state (including NOT RUN / BLOCKED items).
- Remaining risk and missing inputs.
