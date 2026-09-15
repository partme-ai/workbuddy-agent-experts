# Example 3 — Cross-line configuration parity question

## Prompt

> A sibling team on ddd4j-quarkus 3.3.x gave us their CDI/config setup to paste into our 4.0.x service. It's the same framework, so it should just work, right?

## What the skill should do

1. Refuse to confirm parity from the line names alone; the two lines are verified per line.
2. Read the relevant configuration/registration source in **both** lines (3.3.x on Quarkus Platform 3.37.4 / ddd4j 2.0.x, 4.0.x on Quarkus Platform 3.38.2 / ddd4j 3.0.x) and compare the actual symbols and property keys.
3. Report one of three outcomes per item: identical, different (with the diff), or absent in the target line.
4. Remind that CDI discovery is build-time on both lines — a config class that resolves on one line can still fail Arc validation on the other if a bean-defining annotation or producer is missing.
5. Mark unverified parts explicitly rather than guessing.

## Expected output

```
Question: is the 3.3.x CDI/config setup portable to 4.0.x?

Evidence:
  - 3.3.x: runtime module config mapping reads quarkus.* keys A, B; SubjectProvider produced via CDI producer.
  - 4.0.x: same keys present; producer signature identical; ddd4j core symbols renamed (2.0.x → 3.0.x diff listed).

Verdict: DIFFERENT — ddd4j 2.0.x type names do not exist in ddd4j 3.0.x as pasted; the quarkus.* keys match.
Evidence status: SOURCE (both lines read) — 4.0.x build NOT RUN.
Missing: 4.0.x Arc build proving discovery; how to provide: run the 4.0.x build/tests on this SHA.
```

## Failure the skill must avoid

Answering "same framework, so yes — paste it in." The ddd4j major version moved under the same line-family name; cross-line copying without reading both sources is the exact assumption this skill prevents.
