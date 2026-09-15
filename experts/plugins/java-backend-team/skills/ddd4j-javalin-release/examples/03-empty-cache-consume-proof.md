# Example 3 — Proving clean-cache consumption from the private repo

## Prompt

> The deploy logs look fine but QA says they can't build from the private repo. Give me hard evidence one way or the other that 7.1.x artifacts are actually consumable.

## What the skill should do

1. Distinguish the evidence tiers: deploy log success is producer-side; consumption must be proven with an isolated temporary Maven repository and `-U`, independent of the producer reactor and any warm `~/.m2`.
2. Run the consumer proof: resolve the published coordinates — parent, BOM, and a representative runtime plus integration artifact — and compile a minimal independent consumer.
3. Validate provenance: expected version, timestamped SNAPSHOT origin, POM model appropriate to 7.1.x (Maven 3/POM 4.0), and checksum/sidecar integrity where exposed.
4. Report PASS/FAIL per validation item and, on failure, capture the exact resolution error class — not a guess.

## Expected output

```
Empty-cache consumption proof: 7.1.x @ SHA def456

Isolated repo: /tmp/consumer-m2 (empty), settings: private remote by name only.
Consumer: minimal project, dependency:go-offline + compile with -U.

| Check                                | Result |
|--------------------------------------|--------|
| Parent io.ddd4j:ddd4j-javalin-parent | PASS   |
| BOM import resolution                | PASS   |
| Runtime artifact (web)               | PASS   |
| Integration artifact (testcontainers)| FAIL — 404 on sidecar .sha1 |
| SNAPSHOT provenance (timestamped)    | PASS for resolved artifacts |

Verdict: NOT consumable as a family — integration artifact metadata incomplete.
Deploy log "success" stands, but remote sidecars are missing (partial publish
of the last module). Re-deploy that module and re-run this proof.
```

## Failure the skill must avoid

Reporting "consumable, the deploy completed with exit code 0". The producer-side exit code says nothing about the remote; only the isolated empty-cache run exposed the missing sidecar that breaks QA builds.
