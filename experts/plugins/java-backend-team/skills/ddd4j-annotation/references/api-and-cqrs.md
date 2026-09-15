# API and CQRS Annotations

> Collection date: 2026-09-11.

## API

- **`ApiIdempotent` / `ApiIdempotentType`** — declares the idempotency strategy; behavior is implemented by a Web guard.
- **`ApiModule`** — API module metadata.
- **`ApiOperationLog`** — operation log metadata.
- **`RawResponse`** — intent to skip the unified response wrapper.

## CQRS

- **`CreateEvent`**, **`UpdateEvent`**, **`DeleteEvent`** — method-level event intent.

Track the actual scanner or interceptor for each item. The annotation's existence is not behavior evidence.
