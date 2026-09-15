# Deep FAQ

> Collection date: 2026-09-11.

1. **Which line takes priority for a new project?** The organization's JDK and target runtime decide first, then the highest verified line.
2. **Can Java 17 use ddd4j 3.0.x?** Current 3.0.x requires Java 21.
3. **Can Javalin 7.1.x use Maven 4?** The current formal contract is still Maven 3/POM 4.0.
4. **Is Quarkus 4.0.x Quarkus 4?** No — the current platform is 3.38.2.
5. **Can a Cloud line pair with any Boot?** Primary combinations are locked by the matrix; alternatives need separate verification.
6. **Does a local SNAPSHOT count as available?** It is not remotely consumable.
7. **What if CI did not start due to billing?** Mark BLOCKED; it is neither code failure nor PASS.
8. **What if Security was exempted?** Mark SKIPPED as a risk.
9. **How is remote availability proven?** Consume with -U from an isolated clean Maven repository.
10. **Can a historical line upgrade its JDK?** That is a compatibility change and cannot be decided automatically by the version skill.
11. **Who wins on matrix conflicts?** The current POMs and execution results take priority; fix the matrix scripts in sync.
12. **When is an alternative combination chosen?** When the primary combination cannot satisfy explicit constraints and the alternative has independent evidence.
