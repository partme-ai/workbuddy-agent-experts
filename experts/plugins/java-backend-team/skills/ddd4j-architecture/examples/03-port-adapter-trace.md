# Example 3 — Tracing a port to its registered adapter

## Prompt

> Our `CommandBus.execute` works in tests but throws in production with "no executor registered". The interface exists in core. Walk me through how to find where the wiring should happen.

## What the skill should do

1. Explain the chain: port in core → concrete adapter in the capability module → registration by the runtime module → static facade resolves at call time.
2. Locate the runtime module for the project's DI framework and find the registration point (e.g. Spring's bean lifecycle, Guice `Module`).
3. Check whether the executor's registration runs at all — bean conditions, profile guards, or an earlier startup failure can skip it.
4. Distinguish the three failure classes: missing adapter module, missing registration, registration that silently failed.
5. Give the verification command or test that proves the registration.

## Expected output

```
Port:    CommandBus (core, SOURCE confirmed)
Adapter: OrderCommandExecutor — present in the application module (SOURCE)
Registration: SpringRuntimeModule registers executors after singleton
  instantiation — the OrderCommandExecutor bean is @Profile("dev") guarded,
  so production never registers it. ← root cause

Fix: remove the profile guard or provide a production executor binding.
Verify: runtime-testkit startup test asserting CommandBus resolves the
executor outside the dev profile.

Evidence: SOURCE. Production behavior NOT RUN — flag as remaining gap.
```

## Failure the skill must avoid

Concluding "core is missing a CommandBus API" and proposing a new interface. The port exists; the runtime registration is what failed — misreading this class of failure as a core gap is the exact trap the skill warns about.
