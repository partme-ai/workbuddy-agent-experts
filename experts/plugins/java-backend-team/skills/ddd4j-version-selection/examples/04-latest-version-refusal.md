# Example 4 — Boundary: "just give us the latest"

## Prompt

> Don't overthink it — put the latest ddd4j and the latest Boot on the new project. And while you're at it, use that ddd4j-quarkus 4.0.x line for our Quarkus folks; 4 must be newer and better than 3.38.

## What the skill should do

1. Refuse the latest-by-default: selection is a compatibility tuple — JDK, Maven, ddd4j line, adapter line, framework version — and the JDK constraint comes first. Without the team's JDK there is no answer, only a guess.
2. Correct the 4.0.x misreading: ddd4j-quarkus `4.0.x` is the adapter maintenance line name, pairing with Quarkus Platform 3.38.2 on JDK 21 / Maven 4 — it is not "Quarkus 4" and not comparable to "3.38" as a newer/older pair.
3. Ask for the input contract: new vs upgrade, available JDK and Maven, target runtime, whether Maven 3 / POM 4.0 is mandatory, and whether remote SNAPSHOT consumption is acceptable.
4. Give a tentative candidate under a stated assumption, per the skill's insufficient-input rule, clearly marked.

## Expected output

```
Refusal 1 (latest-by-default): "latest" is not a compatibility answer.
Tentative candidate ASSUMING JDK 17 + Boot: ddd4j 2.0.x + ddd4j-boot 3.5.x
(Boot 3.5.16, Maven 3 / POM 4.0) — marked tentative until you confirm the
JDK and Maven versions.

Correction: ddd4j-quarkus 4.0.x = adapter line name; it pairs with Quarkus
Platform 3.38.2, JDK 21, Maven 4 / POM 4.1. It is not Quarkus 4 and not
"newer than 3.38" in any comparable sense.

Missing: JDK + Maven versions, target runtime per service; how to provide:
`java -version`, `mvn -version`, and the runtime choice per service.
```

## Failure the skill must avoid

Emitting "3.0.x + Boot 4.1 + quarkus 4.0.x" as the "latest stack." Two of those three selections are wrong for most inputs, and the third is a category error — a showcase of every bias the skill exists to intercept.
