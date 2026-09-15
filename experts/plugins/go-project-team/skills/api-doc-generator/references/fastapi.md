# FastAPI discovery

## Locate routes

- Find `FastAPI`, `APIRouter`, `include_router`, router prefixes, tags, dependencies, and mounted applications.
- Read decorator methods such as `get`, `post`, `put`, `patch`, and `delete`.

## Resolve requests and responses

- Inspect function signatures, `Path`, `Query`, `Header`, `Cookie`, `Body`, `Form`, and `File` declarations.
- Resolve Pydantic models, aliases, field constraints, unions, discriminators, and optionality.
- Preserve decorator `status_code`, `response_model`, `responses`, and content types.

## Security and errors

- Follow dependency injection for authentication and authorization.
- Inspect `HTTPException`, exception handlers, middleware, and tests.
- Prefer the application's generated OpenAPI schema when it is checked or reproducibly generated.
