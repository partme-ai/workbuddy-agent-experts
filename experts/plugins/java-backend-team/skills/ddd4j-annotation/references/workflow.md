# Workflow — Adding a New Annotation

A canonical end-to-end flow for introducing or reviewing a ddd4j annotation.

## Step 1 — Define the contract

- Specify the annotation's purpose, target, retention, and defaults.
- Decide which family (DDD / CQRS / API / ORM) it belongs to and which module will own it.

## Step 2 — Implement the annotation

- Add the annotation class with explicit `@Retention`, `@Target`, and `@Documented`.
- Document every attribute with default values.
- Cross-check package name and Java / Jakarta differences for the target line.

## Step 3 — Wire the consumer

- Implement or update the consumer in the Web, Data, or Runtime module.
- Make the consumer behavior observable via existing context (request scope, interceptor, repository hook).

## Step 4 — Test the chain

- Reflective presence test (annotation is findable on the target element).
- Default-value test (defaults match spec).
- Independence test (multiple annotations can coexist on the same element).
- Consumer behavior test (the consumer actually performs the documented behavior).
- Cross-line build test on at least one other maintenance line.

## Step 5 — Document and ship

- Update the annotation's Deep Reference file with the new entry.
- Add an entry to the relevant capability-boundary list.
- Note any privacy or security implications (tenant, audit, log fields).
