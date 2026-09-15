# Workflow — ddd4j-cloud Feign Contracts

A canonical end-to-end flow for service-to-service calls.

## Step 1 — Confirm the source of truth

- Run ddd4j-cloud-version-selection to fix the combination.
- Locate the Feign extension source and tests.

## Step 2 — Wire interceptors

- Register request interceptors that propagate context and tenant headers.
- Confirm header allowlists and no credential leakage.

## Step 3 — Configure errors and retries

- Install the error decoder factory mapping remote errors to the stable contract.
- Configure retries with backoff and idempotency guarantees.

## Step 4 — Manage request cleanup

- Confirm request-scoped resources are restored after each Feign call.
- Cover exception, timeout, and retry terminal states.

## Step 5 — Verify

- Run real Feign round-trips between two services: context, tenant, error, retry.
- Produce a report with interceptor inventory, evidence state, and remaining risk.
