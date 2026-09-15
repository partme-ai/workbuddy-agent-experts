# Example 3 — Evidence request: prove remote consumability

## Prompt

> Ops says the new 3.3.x artifacts "aren't in Nexus" but our builds work fine. Settle it — are the artifacts actually consumable remotely or not?

## What the skill should do

1. Frame the question correctly: local builds passing only proves local availability — a warm local cache can mask a missing remote artifact.
2. Run or specify the decisive check: isolated clean-cache consumption (`-U`, empty local repository) of the exact artifact coordinates from the private repository.
3. Record the coordinates, version, and SHA the check applies to.
4. Interpret outcomes: clean-cache resolve OK → CONSUMED; failure → the artifacts were never published (or the repo config is wrong), regardless of local success.
5. Report the evidence grading and redact any repository credentials in the output.

## Expected output

```
Question: are 3.3.x artifacts remotely consumable?

Check: clean-cache resolve (isolated empty local repo, -U) of
       io.ddd4j:<artifact>:3.3.x-SHA-version from the private repository.

Result: RESOLVE FAILED — artifact absent from the remote repository.

Verdict: NOT CONSUMED. Local "builds work fine" is warm-cache evidence only and
does not settle the question — this failure indicates the deploy never landed
(or incomplete module inventory at publish time).
Next: re-run publish with the full 61-module inventory check, then re-consume with -U.
Evidence: CONSUME = FAILED (remote); BUILD = local-only, not remote evidence.
```

## Failure the skill must avoid

Declaring "the artifacts are fine, we build them every day." That is precisely the warm-cache illusion — the decisive evidence is a clean-cache resolve, and it failed.
