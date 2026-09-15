# Context and Errors

> Collection date: 2026-09-11.

Propagate Request ID, Trace ID, Tenant, and Subject. Bind at the entry point; restore on `finally` and async completion. Distinguish 400, 401, 403, 404, 409, 415, 422, 429, and 500. The unified payload must not swallow the cause, and must not expose the internal stack trace.
