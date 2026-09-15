# Example 2 — Read-only binding map review

## Prompt

> We inherited a service with six stream bindings across Kafka and RabbitMQ. Review the configuration read-only — we suspect at least one binding points at the wrong destination.

## What the skill should do

1. Stay read-only — reconstruct the binding map from configuration and code.
2. For each function, resolve all three names separately: the function bean name, its binding name (`<function>-<in|out>-<index>`), and the physical destination actually configured.
3. Check binder assignment per binding — Kafka and RabbitMQ defaults differ and must not be assumed.
4. Check `BindingNamingContributor` naming rules were applied, not overridden ad hoc.
5. Flag each mismatch with the exact configuration keys and the corrected mapping.

## Expected output

| Function | Binding | Destination (config) | Binder | Verdict |
|---|---|---|---|---|
| orderPublisher | orderPublisher-out-0 | orders.events | kafka | OK |
| invoiceConsumer | invoiceConsumer-in-0 | *(unset — defaults to binding name)* | rabbit | DRIFT |
| auditConsumer | audit-in-0 (renamed) | audit.old-destination | kafka | MISMATCH |

Evidence: SOURCE + configuration read. No broker round-trip executed — flagged.

## Failure the skill must avoid

Reviewing only "does a destination exist for each function". The inherited drift hides in the default (destination unset → binding name becomes the topic) and in renamed bindings still pointing at the old physical destination.
