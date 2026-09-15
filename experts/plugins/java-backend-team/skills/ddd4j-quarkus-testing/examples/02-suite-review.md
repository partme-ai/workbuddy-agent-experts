# Example 2 — Read-only test suite review

## Prompt

> Look over our QuarkusTest suites read-only. Are they honest — real containers, proper lifecycle, skips recorded properly?

## What the skill should do

1. Stay read-only and fix the line/SHA first.
2. Inventory the QuarkusTest suites and their QuarkusTestResource classes; check lifecycle assumptions (per-class default, explicit `@QuarkusTestResource.Lifecycle` where needed).
3. Identify which suites need Docker/Testcontainers and how their unavailability is handled.
4. Check evidence hygiene: are skips recorded BLOCKED/SKIPPED, and are JVM and native runs distinguished?
5. Report gaps against what each suite claims to prove.

## Expected output

| Check | Finding | Verdict |
|---|---|---|
| TestResource lifecycle | shared Kafka resource assumed one-time startup; per-class default restarts it per class | **DEFECT** (state loss + slow) |
| Docker handling | Testcontainers suites catch unavailability → log-and-pass | **FALSE GREEN** |
| JVM/native separation | native runs reported with JVM runs merged | **GAP** |
| Arc validation | registration assertions present | OK |

Suite inventory: 14 JVM suites, 3 container suites, 1 native suite (skipped silently last run).

## Failure the skill must avoid

Signing off on "all tests pass". The log-and-pass Docker handler converts infrastructure absence into fake green — the exact opposite of the evidence discipline this skill enforces.
