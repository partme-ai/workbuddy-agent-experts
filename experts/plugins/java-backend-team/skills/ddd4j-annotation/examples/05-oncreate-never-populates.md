# Example 5 — `@OnCreate` timestamps never populate

## Prompt

> Every row we insert has `createdAt` = null despite `@OnCreate` on the field. The annotation is definitely there — I can see it in the class. What's going on?

## What the skill should do

1. Diagnose: annotation presence is not population. `@OnCreate` requires an interceptor or repository hook in the data adapter to run on insert.
2. Check the actual insert path — which repository/interceptor chain executes, and is the audit handler registered in it?
3. Check the second most common cause while there: writes that bypass the adapter (raw SQL, direct mapper calls) skip the hook entirely.
4. Point to the fix: register the audit consumer in the data adapter, then re-test with a real insert.

## Expected output

```
Finding: `@OnCreate` on OrderPO.createdAt has no registered consumer.
Evidence:
  - OrderPO.java line NN — annotation present (SOURCE)
  - Data adapter interceptor chain — audit handler NOT registered (SOURCE)
  - Reflection test passes, which is why the suite stayed green

Impact: every insert path through this adapter leaves createdAt null.
Raw mapper inserts would bypass the hook even after registration.

Fix: register the create/update audit interceptor in the data module, then run
an insert test against a real database. Evidence status: SOURCE only —
behavior test NOT RUN.
```

## Failure the skill must avoid

Telling the user to "check the annotation spelling" or adding a second annotation. The metadata is fine; the missing piece is the adapter-side consumer that turns the annotation into behavior.
