# Outbox and Transactions

> Collection date: 2026-09-11.

1. Business write, domain event, and Outbox row share one transaction.
2. Relay claims atomically.
3. Confirm after a successful send.
4. Backoff and retry on failure.
5. Send to dead-letter after exceeding the limit.
6. Consume and publish are idempotent by event / message id.
7. Crash-recovery tests cover the windows after claim, after send, and before confirm.
