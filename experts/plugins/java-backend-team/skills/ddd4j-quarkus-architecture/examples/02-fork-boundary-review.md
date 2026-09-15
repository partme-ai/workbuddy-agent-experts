# Example 2 — Read-only fork boundary review

## Prompt

> We forked ddd4j-quarkus to add a private auth tweak. Before we propose upstreaming, review the module boundaries read-only and tell us what we broke.

## What the skill should do

1. Stay read-only — this is a boundary review, not a refactor.
2. Fix the line and SHA, then map the fork's modules against the upstream list: parent, bom, dependencies, extension-parent, auth, data, mq, web, cache, extensions, samples.
3. Check runtime/deployment separation for every touched extension.
4. Check dependency direction: no feature module may reach into another feature module's internals; consumers go through bom/dependencies.
5. Report violations with file-level evidence and proposed fixes.

## Expected output

| Module | Violation | Evidence | Suggested fix |
|---|---|---|---|
| `auth-runtime` (fork) | build step class added to the runtime module | `AuthBuildStep` in runtime `src/main/java` | move to deployment module |
| `web` (fork) | imports `auth-deployment` internals | import of deployment-only package in `WebContextFilter` | depend on auth runtime SPI only |

Checked and clean: parent/bom versions match the line; extensions/ and samples/ untouched; CDI scopes unchanged.
Not verified: no QuarkusTest run on the fork SHA.

## Failure the skill must avoid

Declaring "boundaries are fine" because the module list matches upstream. The fork's violations are inside modules, not between them — the review must read imports and module contents, not just names.
