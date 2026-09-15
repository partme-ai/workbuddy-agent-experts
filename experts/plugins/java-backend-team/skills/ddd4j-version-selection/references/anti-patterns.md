# Anti-Patterns

> Collection date: 2026-09-11.

1. **Latest-version bias**: recommending 3.0.x without collecting JDK/runtime; fix constraints first.
2. **Branch-name inference**: treating quarkus 4.0.x as Quarkus 4; read quarkus-bom.version.
3. **Toolchain flattening**: moving everything to Maven 4; keep Maven 3/POM 4.0 on old lines.
4. **Incomplete combinations**: giving only ddd4j without Boot/Cloud/Javalin/Quarkus and framework versions.
5. **False green release**: calling a local build or an upload start consumable; require remote clean-cache verification.
6. **Stale matrix**: copying historical tables without a date/SHA; re-read the source every time.
