# OpenAPI-first discovery

Use the checked-in OpenAPI document as the contract authority, then compare it with generated output and implementation.

## Locate

- Search for `openapi.yaml`, `openapi.json`, `swagger.yaml`, generator configuration, and contract tests.
- Resolve `$ref` values across files before documenting schemas.
- Preserve `servers`, base paths, tags, security schemes, operation IDs, parameters, request bodies, responses, callbacks, and webhooks.

## Verify

- Validate the contract with the project's configured linter when available.
- Compare implemented routes against contract operations in both directions.
- Report undocumented implementation routes and unimplemented contract operations separately.
- Treat generated documentation as output, not as stronger evidence than the source contract.

## Avoid

- Do not flatten polymorphic schemas without explaining `oneOf`, `anyOf`, or discriminators.
- Do not assume every response is JSON.
- Do not invent examples for fields marked secret, token, password, or personal data.
