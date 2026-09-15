# Gin API discovery

## Locate routes

- Find `gin.New`, `gin.Default`, route groups, nested `Group` prefixes, and HTTP method registrations.
- Trace handler variables and registration helper functions.

## Resolve contracts

- Inspect `Param`, `Query`, `GetHeader`, `Cookie`, `ShouldBind*`, and bound structs.
- Read `binding` and validation tags plus custom validators.
- Follow response DTOs and helpers used with `JSON`, `XML`, `YAML`, files, or streams.

## Middleware and errors

- Include group/global middleware for authentication and authorization.
- Inspect abort status calls, centralized error middleware, and tests.
- Do not assume every `error` value maps to HTTP 500; follow actual branches.
