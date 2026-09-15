# Publication and Consumption

> Collection date: 2026-09-11.

1. Run a clean build with the full test suite.
2. Deploy modules serially; record the total module count and the exit code.
3. Verify remote metadata, timestamped SNAPSHOT, and sidecar artifacts.
4. Create an isolated local Maven repository and use `-U`.
5. Consume `parent`, `dependencies`, BOM, and a representative JAR.
6. Report CI, Security, and production acceptance as separate gates.

An RFC 9457 JSON 404 or a mid-sequence module failure is `PARTIAL`, not `PASS`.
