# Anti-patterns and deep FAQ

## Anti-patterns

### 1. Normalize every branch to the newest toolchain

Bad: convert 7.1.x to Maven 4 because 7.2.x uses it.

Better: derive each line’s ddd4j/JDK/Maven/POM contract and adapt shared behavior without changing the compatibility baseline.

### 2. Mark plan tasks complete from filenames or checkboxes

Bad: a runtime class exists, so lifecycle hardening is done.

Better: trace startup/readiness/drain/close behavior and require executed failure/rollback/idempotency tests before correcting task status.

### 3. Treat infrastructure activity as acceptance

Bad: push succeeded, Actions started, or Maven printed uploads, therefore the release passed.

Better: prove final remote SHA, terminal required-job conclusions, successful complete deploy inventory, remote metadata, and isolated empty-cache consumption separately.

### 4. Diagnose every CI rejection as code or secret failure

Bad: repeatedly rotate credentials when the job never started due to billing.

Better: quote the sanitized infrastructure reason, mark CI blocked, preserve existing secrets, and use an authorized local fallback without relabeling CI green.

### 5. Copy a Javalin 6 implementation into Javalin 7

Bad: transplant route configuration and tests verbatim.

Better: preserve the observable contract while adapting framework API differences, then run each line on its real toolchain.

## Deep FAQ

1. **What if the repository has both Spec Kit and OpenSpec?** Use the artifacts already owning this change. If both claim it and ownership is unclear, do not create or overwrite specs; ask the user to choose.
2. **What if only a Superpowers plan exists?** Continue it as the active fact source. Do not initialize another SDD system without authorization.
3. **What if the worktree is dirty?** Inventory and preserve user changes. Work around non-overlapping edits; stop if the requested change would overwrite ambiguous user work.
4. **What if CodeGraph is absent?** Skip it; use `rg`, source reading, tests, and build evidence. Do not initialize indexing on the user’s behalf.
5. **How should optional dependencies affect readiness?** Follow the approved contract. Typically required dependency failure prevents readiness/startup, while optional failure yields an explicit degraded status, never a silent READY.
6. **Can Caffeine remain?** Yes only as an explicitly documented single-instance/development fallback. Multi-instance production requires a proven shared atomic/CAS implementation.
7. **What if Docker is unavailable?** Mark container verification blocked and continue safe source/unit checks. Do not call skipped or zero-test execution green.
8. **What if Maven fails before tests start?** Classify dependency/toolchain/model failure separately; inspect effective POM and remote availability before changing product code.
9. **Can a partial Maven deploy be resumed?** Only after identifying the failed module and remote state. Use repository-supported recovery and revalidate the complete inventory afterward.
10. **When is production hardening complete?** Only when the approved behaviors, regressions, branch contracts, CI/release gates, and required runtime acceptance have evidence. Otherwise report the exact remaining gate.
11. **How should sensitive logs be shared?** Redact credentials, tokens, settings content, authorization headers, and signed private URLs; retain only non-secret error class, status, coordinate, module, and timing evidence.
12. **Can upstream ddd4j be changed?** Only when current Javalin evidence proves the blocker and the user authorizes the expanded scope. Otherwise document the dependency blocker and keep Javalin scope intact.
