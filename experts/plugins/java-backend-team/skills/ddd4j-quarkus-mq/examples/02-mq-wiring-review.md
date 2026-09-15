# Example 2 — Read-only MQ wiring review

## Prompt

> Audit our messaging setup read-only. We're on ddd4j-quarkus 4.0.x with NATS. I want to know where we'd lose or duplicate messages.

## What the skill should do

1. Stay read-only and fix the line/SHA (4.0.x → Quarkus Platform 3.38.2 / ddd4j 3.0.x / JDK 21 / Maven 4).
2. Inventory `MQClient` and listener registrations; flag optional registrations that silently no-op when the broker is absent.
3. Trace ack/nack sites: does any path ack before the business effect is committed?
4. Check retry/DLQ policies and consumer idempotency for redeliveries.
5. Check lifecycle: drain, reverse-order close, idempotent close across startup/shutdown observers.

## Expected output

| Check | Finding | Verdict |
|---|---|---|
| Registrations | 2 listeners required, 1 optional (silently skips if broker down) | OK / note |
| Ack timing | `OrderAck` acks on receipt, handler commits after | **LOSS RISK** |
| Retry/DLQ | no retry limit on `InventoryListener` — infinite requeue | **RISK** |
| Idempotency | no dedupe key; redelivery applies the effect twice | **GAP** |
| Lifecycle | drain present; close not idempotent (double close on error) | GAP |

Evidence: SOURCE read of MQ wiring. Testcontainers round-trips NOT RUN on this SHA.

## Failure the skill must avoid

Summarizing "messaging looks fine, tests pass in CI". The CI suite cannot expose ack-on-receipt loss or infinite requeue — those need failure-path reading plus real-broker round-trips.
