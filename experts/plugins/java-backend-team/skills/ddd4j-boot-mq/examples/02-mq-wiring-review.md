# Example 2 — MQ wiring review (read-only)

## Prompt

> We deploy next week and messaging is the risky part. Read-only review of the boot MQ setup: listeners, retries, dead letters, shutdown. Tell us what would break at 3am.

## What the skill should do

1. Stay read-only; findings with severity, not patches.
2. Fix the line, then read the MQ AutoConfiguration, Properties, listener registrar, and every listener the application declares.
3. Classify each listener as required or optional and check the startup-failure behavior matches the intent.
4. Check every consumer for a bounded retry plus dead-letter path, and for idempotency under redelivery.
5. Check shutdown ordering and idempotent close for producers and listeners.

## Expected output

| Check | Finding | Severity |
|---|---|---|
| Listener scan | 2 listeners declared, registrar finds both | OK |
| Required/optional | both optional; a broker outage at deploy starts with zero consumers, silently | High |
| Retry/DLQ | `payment-events` consumer: retry configured, no dead letter → poison message loops forever | Critical |
| Idempotency | consumer state update not idempotent; duplicates expected under at-least-once | High |
| Shutdown | producer close registered; listener container close not idempotent | Medium |

Evidence: SOURCE read on line <L>. No broker tests executed — read-only review.

## Failure the skill must avoid

Reporting "messaging looks configured" from the presence of the starter and annotations. The 3am failure here is the retry loop without a dead letter — invisible in every happy-path test and triggered by one malformed payload.
