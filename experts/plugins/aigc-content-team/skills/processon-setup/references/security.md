# Security boundary

## Storage location

- macOS and Linux: `$XDG_CONFIG_HOME/processon/credentials.json`, defaulting to `~/.config/processon/credentials.json` when the variable is not set.
- Windows: `%APPDATA%\processon\credentials.json`.
- On Unix the directory mode is `0700` and the file mode is `0600`.
- `PROCESSON_CONFIG_PATH` is only for isolated tests or controlled advanced deployments.

## Data flow

The local page submits user input to the same loopback service. The setup script atomically writes the raw Token to the user directory. The stdio proxy reads the Token and adds `Authorization: Bearer` to requests sent to `https://smart-hd.processon.com/mcp`; the Token is never sent to any other origin.

## Rotation and failure

To rotate, run `python3 scripts/processon_setup.py ui` again, save the new value, and reopen the host application. HTTP 401 triggers exactly one local re-read; a second failure becomes `PROCESSON_AUTH_REQUIRED`. When a generation call hits a connection interruption, HTTP 408, or 5xx, the state is unknown: stop and coordinate instead of blindly replaying.

## Privacy checks

- Check only that the credential exists; never read or print its contents.
- Never leave the Token in screenshots, clipboard history, terminal arguments, exception traces, or acceptance reports.
- Real acceptance records only the time, protocol result, tool names, and non-sensitive artifact identifiers.
- When the user asks to delete the credential, confirm the exact user-level path and recoverability before acting.
