# Example 4 — "While you're in the routes, add authentication"

## Prompt

> You're already touching the route setup — just add login handling to these endpoints while you're there. Standard username/password, keep it simple.

## What the skill should do

1. Decline the inline auth addition: authentication framework selection, token validation, and role mapping belong to `ddd4j-javalin-auth`, and a hand-rolled login inside route handlers would bypass the `SubjectProvider` contract and per-request Subject cleanup.
2. Name the concrete risk: an ad-hoc check in one handler produces 401 semantics that differ from the rest of the service and never releases the Subject on the pooled thread.
3. Hand off with the install pattern and state what this skill will do after: wire the returned contract into route protection and error mapping consistently.
4. Record the routing decision in the output.

## Expected output

```
Out of scope here: authentication belongs to ddd4j-javalin-auth
(SubjectProvider selection, token validation, 401/403 semantics, Subject cleanup).
Install: npx skills add full-stack-skills/ddd4j-skills --skill ddd4j-javalin-auth

Rationale: a username/password check inside a route handler creates a second
auth authority with its own 401 behavior and no Subject lifecycle.

This skill takes over after: protecting the routes with the auth contract
(matchers, error mapping, async paths) and adding the HTTP contract tests.
```

## Failure the skill must avoid

Adding a "simple" password check inline in the handler because the route file was already open. It works for the demo, then coexists with the real `SubjectProvider` — two auth authorities, one service, and a Subject that is never cleaned from pooled threads.
