# Workflow — ddd4j Extension Integration

A canonical end-to-end flow for adding an optional ddd4j extension.

## Step 1 — Confirm the source of truth

- Read the current root POM and directory listing to confirm which extensions exist.
- Identify the target extension (excel, license, monitor, otel, pf4j, qlexpress, qrcode, validation).

## Step 2 — Verify the module

- Confirm the artifact exists in the current maintenance line.
- Note external dependencies (license server, plugin directory, OTel collector).

## Step 3 — Wire conditionally

- Add the dependency as optional.
- Implement the classpath guard and the enabled switch in runtime/Boot auto-configuration.
- Preserve user Bean overrides.

## Step 4 — Sandbox risky inputs

- Restrict QLExpress functions, access, and timeouts via builder permissions.
- Apply signature, origin, isolation, and permission policies to PF4J plugins.
- Never log license keys or secrets.

## Step 5 — Test and degrade

- Run real behavior tests: normal, disabled, classpath-missing, and shutdown.
- Confirm disabling the extension degrades without breaking core.

## Verify

- Confirm resource owners and close semantics.
- Produce a report with the extension choice, assembly points, evidence state, and remaining risk.
