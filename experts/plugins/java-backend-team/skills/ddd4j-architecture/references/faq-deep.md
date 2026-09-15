# Deep FAQ

> Collection date: 2026-09-11.

1. **Can core depend on Jackson?** Follow the `CoreIndependenceTest` and the POM allowlist.
2. **Is annotation a runtime concern?** Annotation retention and consumers decide; do not assume uniformly.
3. **Does Repository belong to data?** The port lives in core; the implementation lives in data.
4. **Does CommandBus belong to runtime?** The interface lives in core; wiring lives in runtime.
5. **Can Web modify Domain Context directly?** Bind and release only through a controlled scope.
6. **Does a BOM import mean a Bean is available?** No.
7. **Can aggregate modules contain code?** Follow the current POM and source. Typically they are aggregation boundaries only.
8. **How do we verify the architecture?** Combine CodeGraph, ArchUnit / rule tests, and compile + runtime layered validation.
9. **Can Spring and Guice coexist?** Only if registration ownership is explicit to avoid duplicate SPI bindings.
10. **Does identical cross-line structure imply identical behavior?** No — behavior and runtime evidence are required.
