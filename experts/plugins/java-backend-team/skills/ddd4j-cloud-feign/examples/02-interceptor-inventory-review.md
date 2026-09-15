# Example 2 — Read-only Feign plumbing review

## Prompt

> Audit our Feign setup read-only: interceptors, error decoding, retry config. We've been bitten by mystery headers before.

## What the skill should do

1. Stay read-only — inventory and findings, no changes.
2. Enumerate every Feign client, its registered interceptors, and their ordering.
3. Diff each client's outbound headers against the intended allowlist; flag anything that forwards credentials.
4. Check error decoding goes through the factory rather than per-caller try/catch, and that retry policies declare idempotency per endpoint.
5. Verify cleanup covers exception, timeout, and retry terminal states — success-only cleanup is a finding.

## Expected output

| Client | Interceptors (order) | Header issues | Retry | Cleanup |
|---|---|---|---|---|
| InventoryClient | context → tenant | OK | 2× backoff, idempotent GET only | OK |
| PaymentClient | none | missing tenant | retries POST — non-idempotent | success only |

Findings: PaymentClient violates three rules. Evidence: SOURCE only; round-trip tests NOT RUN.

## Failure the skill must avoid

Scanning for interceptors and stopping when some are found. The defects live in the details the presence check misses: per-caller error decoding, a retrying POST, and cleanup that never runs on the timeout path.
