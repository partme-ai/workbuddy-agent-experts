# Anti-patterns and corrections

## 1. Collecting the Token in chat

- Wrong: ask the user to send the Token to chat so the assistant can configure it.
- Right: open the loopback setup page and let the user save the Token in the password field themselves.

## 2. Putting the Token in project or plugin configuration

- Wrong: hard-code a fixed Authorization value in versioned configuration.
- Right: let `.mcp.json` only launch the stdio proxy, and keep the credential in the user config directory.

## 3. Auto-replaying generation after an authentication failure

- Wrong: call the generation tool again after a timeout, HTTP 408, or HTTP 5xx.
- Right: return `UNKNOWN_WRITE_RESULT` and confirm whether the diagram was actually produced first.

## 4. Using logs to prove a successful configuration

- Wrong: print the Token prefix, length, file contents, or full request headers.
- Right: emit only `configured`, `missing`, and safe protocol verification results.

## Hard prohibitions

- Never pass the Token as a command-line argument.
- Never edit a shell profile or system environment variable as part of the default install.
- Never copy another user's credential file.
- Never delete or migrate user data automatically.
- Never follow a redirect that leaves the official ProcessOn endpoint.
