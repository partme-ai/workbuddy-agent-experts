# Workflow — ddd4j-cloud Tenant Isolation

A canonical end-to-end flow for multi-tenant isolation in Spring Cloud.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combination.
- Locate the data tenant, MyBatis, and Feign tenant modules.

## Step 2 — Map the isolation surface

- Identify where the tenant id enters (request header, token), the TenantContextHolder, and the ignore rules.
- Identify where SQL filtering applies and which tables are exempt.

## Step 3 — Verify propagation

- Confirm tenant propagation across sync, async, Reactor, and Feign calls.
- Confirm system-context semantics for background and cross-service operations.

## Step 4 — Test

- Run isolation tests: cross-tenant reads blocked, data scope enforced, ignore rules respected.
- Cover exception, async, and Feign round-trips.

## Step 5 — Report

Produce a single report containing:

- Isolation map (entry → holder → filter → propagation) with file paths.
- Ignore-rule inventory and justification.
- Tests executed and evidence state per tier.
- Violations and risks with proposed fixes.
