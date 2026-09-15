# Example 1 — Choosing a primary combination for a new service

## Prompt

> We're starting a new ddd4j service on Spring Cloud 2023.0.x. Which Boot parent and ddd4j line should we use, and are there any acceptable alternatives?

## What the skill should do

1. Read the eight-line matrix entry for 2023.0.x and extract the primary Cloud→Boot→ddd4j combination.
2. Confirm the pairing against the 2023.0.x branch POMs and `verify_cloud_release_matrix.py`, not from the branch name or README.
3. List compatible alternatives separately, stating explicitly that an alternative is not the primary combination.
4. Enumerate external dependencies the line requires (database, Nacos, Sentinel as applicable) and mark which have no behavior evidence yet.
5. Report the evidence state per tier and list any missing inputs.

## Expected output

```
Selected line: 2023.0.x
Primary combination: <Cloud 2023.0.x> → <Boot parent from matrix> → <ddd4j line from matrix>
  Source: 2023.0.x branch POMs + verify_cloud_release_matrix.py (SOURCE, read)
Compatible alternatives: <listed separately, each with its own pairing>
External dependencies: MySQL, Nacos, Sentinel — connectivity NOT VERIFIED
Remaining risk: none verified at runtime yet; build + CI check pending.

Missing: acceptance behavior for the target services;
how to provide: run the line's compatibility tests and attach results.
```

## Failure the skill must avoid

Guessing the Boot parent from the branch name (e.g. "2023.0.x must use the newest Boot") instead of reading the matrix and POMs, or presenting a compatible alternative as if it were the validated primary combination.
