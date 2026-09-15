# Example 5 — Version numbers copied from another line

## Prompt

> We copied the version block out of our Hoxton.x service into our 2023.0.x service and now the build can't find the ddd4j artifacts. What happened?

## What the skill should do

1. Recognize the classic cross-line copy: Hoxton.x and 2023.0.x pin different Boot parents and ddd4j lines.
2. Read both lines' POMs and diff the version blocks instead of assuming which coordinate is missing.
3. Separate three failure classes: wrong pairing (fix the POM from the matrix), missing upstream artifact (BLOCKED(upstream)), and infrastructure (BLOCKED(infrastructure) if the build environment cannot reach the repository).
4. Produce the corrected 2023.0.x combination from the matrix, with the old `cmpt`/`extensions` naming checked too.
5. Mark which claims are source-read facts and which still need a build to confirm.

## Expected output

```
Root cause: version block copied from Hoxton.x — Boot parent and ddd4j
coordinates belong to a different line.

Diff (Hoxton.x vs 2023.0.x):
  Boot parent:      <hoxton value> → <2023.0.x value>
  ddd4j line:       <hoxton value> → <2023.0.x value>
  Naming:           <old cmpt present: yes/no>

Fix: re-pin the 2023.0.x service from the matrix, not from the sibling POM.
Evidence: SOURCE (both branches' POMs read). Corrected build NOT RUN —
run the build and CI check before closing.
```

## Failure the skill must avoid

"Fixing" the build by upgrading the missing ddd4j artifact to the newest version. That creates an unverified hybrid of two lines; the correct fix is to take the whole 2023.0.x combination from the matrix.
