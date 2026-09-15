# Example 5 — Deploy logs said success, consumers get 404

## Prompt

> Last night's 7.2.x deploy printed every module uploading and finished clean, but this morning the consumer pipeline 404s on `ddd4j-javalin-data`. The repo admin says nothing is wrong. Who's right?

## What the skill should do

1. Reframe the dispute: both are half-right — upload log lines are producer activity, not publication success; a 404 on one artifact is a consumer-side fact that demands inspection, not blame.
2. Inspect the specific failure: fetch the 404 response body. A first-time Maven 4 SNAPSHOT publish can fail partway with an RFC9457 JSON 404 after other modules uploaded — the deploy's exit code may still mislead.
3. Check `target/resume.properties` from the deploy run and the remote metadata for `ddd4j-javalin-data`: compare the expected module inventory against what the remote actually serves.
4. Recover correctly: treat it as partial publication, resume/re-deploy the failed module with the repository-supported retry, then re-run the isolated empty-cache consumption proof for the whole family.

## Expected output

```
Dispute resolution: deploy ≠ published.

Evidence:
  - Deploy log: 14 modules uploaded, exit 0 (producer view).
  - Consumer: GET .../ddd4j-javalin-data/4.1.0-SNAPSHOT/maven-metadata.xml
    → 404 RFC9457 JSON {"title":"Not Found",...}   ← first-publish metadata
      never finalized for this module.
  - target/resume.properties: present, records data module as incomplete.
  - Remote inventory: 13/14 modules resolvable.

Verdict: PARTIAL publication. Neither "repo admin is wrong" nor "deploy failed"
— it succeeded partway and must be resumed.

Recovery: resume publish for the data module (-r), verify metadata build number
increment, then re-run empty-cache consumption for all 14 modules.
```

## Failure the skill must avoid

Declaring victory with "the deploy succeeded, so the consumer pipeline must be misconfigured". The upload lines and exit code are exactly the producer-side noise that partial Maven 4 publications hide behind — and the consumer 404 is the truth that needed investigating.
