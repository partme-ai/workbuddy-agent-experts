# Deep FAQ

> Collection date: 2026-09-11.

1. **Should a business project inherit parent or import BOM?** Use `parent` for build conventions; use BOM for versions only.
2. **Can `dependencies` be imported directly by a business project?** Per project contract, BOM is usually the stable consumer surface.
3. **Why does the adapter also have a BOM?** It manages ecosystem-specific artifacts and framework versions.
4. **Can a module pin a version?** Only when ownership is explicit and the layer above does not manage it.
5. **Can POM 4.1 work with Maven 3?** Not as a supported path.
6. **Why does 3.0.x use `<subprojects>`?** Because of the Maven 4 / Model 4.1 contract.
7. **Does an effective POM passing mean the build runs?** No.
8. **Does a resolvable BOM mean every JAR is available?** No.
9. **How do I check import conflicts?** Run the project scripts and inspect the effective POM and dependency tree.
10. **Can `enforcer.skip` be used for release?** No — it can only serve as a scoped diagnostic.
