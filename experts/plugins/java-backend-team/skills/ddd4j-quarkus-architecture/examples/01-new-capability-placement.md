# Example 1 — Place a new capability in the module tree

## Prompt

> We're adding tenant propagation to ddd4j-quarkus. Which module should it live in, and what does it touch?

## What the skill should do

1. Fix the line first (3.3.x or 4.0.x) — the module layout is verified per line.
2. Walk the module map: parent, bom, dependencies, extension-parent, auth, data, mq, web, cache, extensions, samples.
3. Recommend placement as a runtime/deployment pair under `extensions` unless the capability extends an existing feature module (e.g., tenant context is closest to auth/web context binding).
4. State the allowed dependency direction: the new module may depend on core contracts and extension-parent; the bom/dependencies modules register it for consumers.
5. List the verification the placement requires (Arc wiring, QuarkusTest, native boundaries).

## Expected output

```
Placement: tenant propagation → runtime/deployment pair under extensions/
  (context binding hooks stay in the auth/web modules via CDI, not by importing web into the extension).

Dependency direction:
  tenant-extension (runtime)  → ddd4j core contracts, extension-parent
  tenant-extension (deployment) → tenant-extension (runtime) + BuildItem producers
  bom / dependencies            → register both artifacts

Touches: bom (version entry), dependencies (consumer convenience), samples (one usage demo).
Verification: Arc build-time discovery, QuarkusTest request-scope tests, native-mode check.
```

## Failure the skill must avoid

Telling the team to put the tenant build steps (BuildItem producers, Recorder calls) inside the runtime module. Build steps live in the deployment module; the runtime module never appears on the build classpath.
