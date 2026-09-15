# ACK, Retries, and Dead Letters

> Collection date: 2026-09-11.

- Ack when business processing succeeds and the acknowledgment is open/unconfirmed.
- Nack on business exception; policy decides whether to requeue.
- Retries record attempts, next attempt, and the last error.
- Exhausted retries enter the dead letter.
- A reliable bridge such as an Outbox is needed between producer send and the business transaction.
- Consumers are idempotent by message/event id.
