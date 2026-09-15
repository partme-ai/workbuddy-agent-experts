# Example 1 — Choosing a maintenance line for a new service

## Prompt

> We're starting a new ddd4j-javalin service. Our CI images have JDK 21 and Maven 4 available. Which maintenance line should we target, and what exactly do we need to pin?

## What the skill should do

1. Match the toolchain against the three line tuples: 6.7.x → Javalin 6.7/ddd4j 1/JDK 17/Maven 3; 7.1.x → Javalin 7.1/ddd4j 2/JDK 17/Maven 3; 7.2.x → Javalin 7.2/ddd4j 3/JDK 21/Maven 4.
2. Recommend `7.2.x` for JDK 21 + Maven 4, and name the alternatives if the org later needs to stay on JDK 17.
3. List what to pin: branch (`feature/7.2.x`), Javalin 7.2, ddd4j 3.0.x dependency line, JDK 21, Maven 4 with POM 4.1 `<subprojects>`.
4. Require verification via `BuildLineContractTest` and the current root POM before any code is written.

## Expected output

| Option | Tuple | Fit for JDK 21 + Maven 4 |
|---|---|---|
| 7.2.x (recommended) | Javalin 7.2 / ddd4j 3 / JDK 21 / Maven 4, POM 4.1 `<subprojects>` | Exact match |
| 7.1.x | Javalin 7.1 / ddd4j 2 / JDK 17 / Maven 3 | Would need a toolchain downgrade |
| 6.7.x | Javalin 6.7 / ddd4j 1 / JDK 17 / Maven 3 | Would need JDK 17 and Javalin 6 APIs |

Plus: pin list, and the evidence requirement — confirm the checkout with `BuildLineContractTest` before implementation starts.

## Failure the skill must avoid

Recommending "Javalin 7" generically without the full tuple, which lets a team pair Javalin 7.2 with Maven 3 and ddd4j 2 and discover the incompatibility only at build or runtime.
