# Evidence and Gates

> Collection date: 2026-09-11.

## Status hierarchy

1. SOURCE: POMs, matrix, and source code exist.
2. TEST: target build/behavior tests actually executed.
3. CI: required jobs for the final SHA succeeded in terminal state.
4. PUBLISHED: full deploy exited zero and remote metadata is complete.
5. CONSUMED: isolated clean cache resolved and compiled from the private repository.
6. PRODUCTION: real deployment and production acceptance.

A lower level must not substitute for a higher one.

## Pre-selection checks

- git branch --show-current
- git status --short --branch
- java -version
- ./mvnw -version
- Root POM modelVersion, revision, java.version
- Adapter project framework/BOM versions
- CI and private repository target coordinates

## Currently collected SHAs

| Repository/Line | SHA |
|---|---|
| ddd4j 1.0.x | d9149cb0371cf24328822c17596a408bde3562a5 |
| ddd4j 2.0.x | bbf3dfa330c083ccccafdfe1ac2c266a74513a27 |
| ddd4j 3.0.x | 0699b19917575ebd263182d0fc43457b1aff56db |
| ddd4j-boot 4.1.x | 2c41353821b9c4c027a16da71dad7af0d8edb9c2 |
| ddd4j-javalin 6.7.x checkout | 36865c0935c7af3148c98901da62966e60b6be3d |
| ddd4j-quarkus 4.0.x checkout | e899da7e6eecd4d39320982c0141d29f48028915 |
| ddd4j-cloud 2024.0.x | a3a11af917b221d63ebad3c2481e85b7cb2ed270 |

These SHAs only prove the source at collection time; refresh them before use.
