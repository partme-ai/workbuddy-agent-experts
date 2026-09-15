# Example 3 — Can 7.1.x move to Maven 4?

## Prompt

> 7.2.x uses Maven 4 and it looks nicer. Our 7.1.x service has the wrapper updated to Maven 4 already and it builds locally. Is that officially fine?

## What the skill should do

1. State the contract question precisely: the 7.1.x formal contract is Maven 3, and a local build succeeding does not change a contract.
2. Read the 7.1.x line's root POM and wrapper on the current branch to confirm what the line itself declares.
3. Distinguish "happens to build" from "verified per the line contract" — CI, `BuildLineContractTest`, and publishing gates are the evidence tiers.
4. Recommend reverting to the Maven 3 wrapper for 7.1.x, or formally moving the service to the 7.2.x line if Maven 4 is a hard requirement.

## Expected output

```
Question: is Maven 4 supported on 7.1.x?

Contract: 7.1.x → Javalin 7.1 / ddd4j 2 / JDK 17 / Maven 3 (POM 4.0, <modules>).
Maven 4 belongs to 7.2.x, which also requires JDK 21 and ddd4j 3.

Evidence:
  - 7.1.x root POM: declares Maven 3 model (<modules>)  — SOURCE, read
  - Local Maven 4 build: succeeds for you               — LOCAL, NOT a contract gate
  - CI on Maven 4 for 7.1.x: NOT RUN

Verdict: not per contract. Either restore the Maven 3 wrapper on 7.1.x,
or migrate the service to the 7.2.x line (JDK 21 + ddd4j 3 required).
```

## Failure the skill must avoid

Answering "it builds locally, so it's fine". Local build success is not line-contract evidence, and a Maven 4 build of a Maven 3 line can diverge exactly at the publishing and consumption gates.
