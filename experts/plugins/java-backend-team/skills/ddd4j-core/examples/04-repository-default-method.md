# Example 4 — Repository default method trap

## Prompt

> Our aggregate needs a custom `findByStatus` query. The Repository interface seems to have it already — can we just call it?

## What the skill should do

1. Read the actual `Repository` interface in the target line and check whether the method is a default method.
2. Check whether the concrete adapter registered by the data module overrides it.
3. If it is an unoverridden default, state plainly that calling it throws `UnsupportedOperationException`.
4. Point to the correct path: implement the query in the data adapter, or use `Query<M>` with the domain model.

## Expected output

```
Finding: `Repository.findByStatus` is a default method in 2.0.x (Repository.java line NN).
Adapter check: MybatisAggregateRepository in the data module <overrides | does not override> it.
Impact: calling it through the current adapter <works | throws UnsupportedOperationException>.

Recommended path: <either "safe to call, adapter overrides it" or
"declare the query in the data adapter / use Query<M> instead">.
Evidence: SOURCE only. Adapter behavior test NOT RUN.
```

## Failure the skill must avoid

Assuming interface presence equals working behavior. `Repository` is an ORM-agnostic SPI; whether an operation works depends entirely on the registered adapter.
