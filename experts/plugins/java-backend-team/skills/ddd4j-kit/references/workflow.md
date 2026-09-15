# Workflow — Adopting a ddd4j Utility

A canonical end-to-end flow for selecting and applying ddd4j Kit utilities.

## Step 1 — Search Kit first

- Open `io.ddd4j.kit.*` and look for an existing class that matches the need.
- If the same helper exists in multiple families, prefer the narrowest one (e.g. `ArrayKit` over `CollKit` for primitive arrays).

## Step 2 — Read the contract

- Read the actual signature, Javadoc, and at least one test in the current branch.
- Note null handling, return type (raw vs `Optional`), exception strategy, and thread safety.

## Step 3 — Match the scenario

- For ordinary JSON, use `JsonKit` default mapper / API.
- For Redis trusted payloads, use `JsonKit.REDIS_OBJECT_MAPPER`.
- For event payloads, use `EventPayloadSerializer` with explicit event classes.
- For Bean operations in the domain layer, use `DomainObjectMapper` rather than `BeanKit`.

## Step 4 — Apply the utility

- Call the narrowest API that satisfies the requirement.
- Preserve `Optional` / exceptions / generics — do not collapse them to `null`.
- Wrap unexpected failures with diagnostic context (input type, target class, call site).

## Step 5 — Test the boundary

- Boundary values: `null`, empty collections, empty strings, edge numeric values.
- Error paths: invalid JSON, mismatched event class, missing identifiers.
- Thread-safety test if the utility is shared across threads.
