# Example 2 — Version governance review (read-only)

## Prompt

> Audit our Maven setup against the ddd4j ownership rules. We keep getting "works on my machine" build diffs between developers and CI.

## What the skill should do

1. Stay read-only — produce findings, not fixes.
2. Classify every POM by role: parent, dependencies, BOM, concrete module; flag responsibility confusion (plugin config in the BOM, versions in modules).
3. Diff declared versions against `ddd4j-dependencies` to find scattered numeric pins and property drift.
4. Check the model syntax per line: `<modules>` on 4.0 lines, `<subprojects>` on the 3.0.x line.
5. Generate the effective POM and compare it with the source POM to expose import-order surprises.

## Expected output

| Location | Finding | Rule |
|---|---|---|
| `sms/pom.xml:31` | literal `<version>4.2.7</version>` on a third-party SDK | versions belong to `ddd4j-dependencies` |
| `ddd4j-bom/pom.xml:18` | `<plugin>` management block | plugin config belongs to `ddd4j-parent` |
| `3.0.x` aggregator | `<modules>` retained | POM 4.1 requires `<subprojects>` |
| effective POM | jackson resolves 2.17.1, source declares 2.18 via property | BOM import order wins — check import order |

Summary: which checks were clean, which scripts to run next (`test_dependency_property_layout.py`, `test_bom_import_conflicts.py`), and that no build was executed (`NOT RUN`).

## Failure the skill must avoid

Reading only the source XML and declaring alignment "correct". The effective POM is what consumers resolve — the jackson mismatch above is invisible without generating it.
