# CI and private Maven release gates

## Authorization boundary

Review/test authorization does not imply branch switching, commit, push, CI changes, credential rotation, or publication. Resolve the exact authorized actions before mutating remote state. Never print secrets or private settings contents.

## Git evidence

Before push, verify exact intended files, clean/known dirty state, branch, commit, and tracking ref. After push, prove local HEAD, tracking ref, and remote ref match. A push event is not CI acceptance.

## GitHub Actions

Find runs for the final pushed SHA and inspect required job conclusions. Preserve these distinctions:

- workflow queued/in progress → `NOT COMPLETE`;
- job did not start because of organization billing/spending limit → `BLOCKED (infrastructure)`;
- Maven/test step failed → `FAIL (code/build)` until classified;
- security gate waived → `SKIPPED (risk retained)`, never `PASS`.

Do not change billing, upgrade plans, rotate `MAVEN_SETTINGS_XML`, or edit workflows merely because Actions is externally blocked. If the user explicitly authorized local release as the fallback, CI remains blocked even if publication later succeeds.

## Serial publication

Publish maintenance lines serially unless the repository’s documented process proves safe parallel publication. Stop on the first partial failure; do not proceed as though the family is complete.

For each line capture:

- branch and exact SHA;
- JDK and Maven version;
- settings source by name/path only, without content;
- complete expected module/coordinate inventory;
- command and terminal exit code;
- remote metadata timestamp/build number and artifact sidecars where available.

Maven 4 and first-time SNAPSHOT metadata can fail after some uploads with an RFC9457 JSON 404. Treat this as partial publication. Inspect the endpoint response and `target/resume.properties`; a repository-validated Wagon transport retry and `-r` resume may be appropriate. Never report success solely because upload lines appeared.

## Empty-cache consumer proof

After a successful deploy, create an isolated temporary Maven repository and resolve the intended coordinates with `-U`. Prefer a minimal independent consumer or `dependency:go-offline`/compile that proves parent/BOM/JAR resolution from the private remote rather than the producer reactor or local cache.

Validate at least:

- expected version and timestamped SNAPSHOT provenance;
- parent and BOM resolution;
- representative runtime and integration artifacts;
- POM model appropriate to the line;
- checksum/sidecar integrity when the repository exposes it.

Local `install`, an existing warm `~/.m2`, or producer-reactor success is not remote-consumer proof.

## Release status table

Report each branch independently:

| Branch | Source/tests | Remote SHA | CI | Deploy | Empty-cache consume | Production acceptance |
|---|---|---|---|---|---|---|
| branch | PASS/FAIL | SHA/mismatch | PASS/FAIL/BLOCKED | PASS/PARTIAL/NOT RUN | PASS/FAIL | VERIFIED/NOT VERIFIED |

Family release is green only when every required row/gate is green. A local fallback release can coexist with blocked CI; say both explicitly.
