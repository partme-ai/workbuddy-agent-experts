# Anti-Patterns

> Collection date: 2026-09-11.

1. **Responsibility confusion** — Plugin config placed in a BOM. Return it to `parent`.
2. **Version leakage** — Concrete modules pin third-party versions. Hand those off to `dependencies`.
3. **Model flattening** — Forcing an old line to POM 4.1. Preserve the toolchain.
4. **Missing effective model** — Only inspecting the source XML. Generate the effective POM.
5. **False-green publish** — A warm cache or upload start is enough. Always verify with a clean cache.
