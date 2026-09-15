# Example 1 — Landing a new capability in the right module

## Prompt

> We're adding SMS notifications to our ddd4j 2.0.x system. Where should the SMS client code live — core, kit, or a new module — and who wires it up?

## What the skill should do

1. Apply the dependency-direction rules: core depends on nothing framework-specific; kit is foundational utilities with no business runtime; capability implementations live in the adapter layer.
2. Recommend an `sms`-style capability module (or extensions placement) that defines its own port, with the concrete provider client behind it.
3. Name the runtime's job: registering the implementation, request scoping, and lifecycle (owner + close).
4. Point out what does not belong: no provider SDK imports in core, and no version pins in the new module that `ddd4j-dependencies` should own.
5. State what evidence is still needed before the placement is confirmed.

## Expected output

```
Placement decision:
  - Port + contracts: new capability module (peer of mq / cache), NOT core.
    Core stays free of provider SDKs.
  - Concrete client: inside the capability module's adapter area.
  - Registration + lifecycle: runtime module for the target DI framework.
  - Versions: owned by ddd4j-dependencies; the module POM carries no numbers.

Evidence: SOURCE read of module POMs and dependency direction. No build run.
Missing: chosen SMS provider and runtime target; how to provide: provider POM
and the runtime module in use.
```

## Failure the skill must avoid

Answering "put it in core next to the other contracts." A provider client in core breaks the dependency-inversion rule the skill exists to enforce, and the mistake only surfaces when a second runtime tries to reuse core.
