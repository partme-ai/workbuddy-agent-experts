# Express API discovery

## Locate routes

- Trace `app.use`, `router.use`, `Router`, and HTTP method calls to resolve nested prefixes.
- Account for route modules exported and mounted elsewhere.
- Include middleware order because it can change authentication, validation, and responses.

## Resolve contracts

- Inspect `req.params`, `req.query`, `req.headers`, `req.cookies`, and `req.body` access.
- Read validation schemas from Zod, Joi, express-validator, Yup, or project-specific middleware.
- Follow serializers and response helpers rather than assuming raw `res.json` shapes.

## Errors

- Inspect `next(error)`, error middleware, async wrappers, and integration tests.
- Mark request/response schemas as inferred when the project lacks explicit schemas.
