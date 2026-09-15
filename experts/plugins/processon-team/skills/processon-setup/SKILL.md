---
name: processon-setup
description: Configure or rotate the local ProcessOn Token for the Codex ProcessOn plugin. Use for first use, missing credential, invalid credential, or when the user asks about ProcessOn Token setup; do not use for creating a Token, managing an account, or handling another user's credential.
---

# ProcessOn Local Credential Setup

Let the user complete one-time setup on a three-step local page; the plugin then connects to ProcessOn automatically. The Token must never appear in chat, command arguments, or project files.

## 30-second quick start

Direct requests that fit:

- "First time using ProcessOn, help me finish setup."
- "ProcessOn says the credential is missing, open the configuration page."
- "My ProcessOn Token expired, help me rotate it."
- “第一次使用 ProcessOn，帮我完成本地设置。”
- “ProcessOn 提示缺少凭据，帮我打开配置页。”
- “我的 ProcessOn Token 已失效，帮我安全更换。”

Execute in this order:

1. From the installed plugin root run `python3 scripts/processon_setup.py check` and decide only by the result.
2. On first use, or whenever `PROCESSON_SETUP_REQUIRED` or `PROCESSON_AUTH_REQUIRED` is returned, wait for the MCP proxy to open the local page automatically. It opens at most once per 10-minute cooldown.
3. Only if the browser does not open, run `python3 scripts/processon_setup.py ui` as the manual fallback.
4. Tell the user to paste the Token only into the local page's password field and click "Save Token".
5. After a successful save, retry the original request; reopen Codex only if the current MCP process does not reload the credential.
6. Run `initialize` and `tools/list` for a non-generation validation; do not probe the credential with a generation call.

Read [setup workflow](references/workflow.md) when you need to execute commands or interpret state. Read [security boundary](references/security.md) for credential invalidation, rotation, or safety questions.

## Exact triggers and routing

| State | Detection | Action | Output |
|---|---|---|---|
| First use (首次使用) | `check` returns missing | Proxy auto-opens the local setup page | Three-step guide, do not request the Token |
| Missing credential (缺少凭证) | `PROCESSON_SETUP_REQUIRED` | Use the auto-opened page; manual `ui` only as fallback | Retry after saving |
| Invalid credential (凭证失效) | `PROCESSON_AUTH_REQUIRED` | Proxy auto-opens the same page for rotation | Do not repeat the upstream response |
| Rotate Token (轮换 Token) | User explicitly asks to update | Reopen the setup page and overwrite the user-level credential | Confirm only the save state |
| Already configured | `check` returns configured | Continue with non-destructive MCP validation | Report availability only |

For multi-task requests, restore the connection first and then resume the user's original diagram priority; do not let the authentication flow change diagram content or authorization scope.

## Prohibited behaviors

- Never display, repeat, search, screenshot, log, or infer the Token; never display credential values.
- Do not ask the user to paste the Token in chat, and never accept another person's credential.
- Never place the credential in the repository, plugin cache, Codex configuration, command arguments, prompts, or logs.
- Never delete a user credential automatically; deletion is a user-data change and requires an explicit request.
- Never auto-replay a generation request after an authentication failure; when the result is uncertain, coordinate first.
- Never claim the ability to create Tokens, access account admin pages, change sharing permissions, or recover an expired credential.

See [anti-patterns](references/anti-patterns.md) for common mistakes and the correct replacement.

## Capability boundary

### ✅ Handles well

- Local three-step credential setup right after installation.
- Safe recovery after a missing or invalid credential.
- Local rotation and read-only availability check for the current user's Token.

### ⚠️ Requires user action or input

- Creating a Token: the user must do this in their own ProcessOn account center.
- Entering the Token: the user must paste it into the local password field themselves.
- Reopening Codex: the user must restart the application so the new MCP session loads the credential.

### ❌ Out of scope

- Retrieving, guessing, or resetting a ProcessOn account password; that goes through ProcessOn's official account flow.
- Configuring another person's or team member's private Token; each user should set their own credential.
- Changing cloud file permissions or account plans; that goes through ProcessOn's official product interface or support.

## Audience and customization

- Normal users use the local page and need no understanding of MCP or environment variables.
- Developers and CI may provide a raw `PROCESSON_MCP_TOKEN` inside a controlled child process; that is an advanced override.
- Teams should let each member save their own Token independently and never share credential files.
- The user may choose Chinese or English explanations, a hidden terminal prompt, or the browser page; safe storage and no-disclosure rules are non-negotiable.

## Frequently asked questions

1. **Why can't I just send the Token in chat?** Conversations can be logged; the local password field is the designated input surface.
2. **Where is it saved?** In the current user's config directory, not the plugin install directory; see the security reference for the exact path.
3. **Will it survive a plugin upgrade?** Yes. The credential is stored separately from the versioned plugin cache.
4. **Can I paste a value that already has `Bearer`?** Yes; the setup normalizes it and stores only the raw Token.
5. **Must I reopen Codex after saving?** Retry first: the proxy reloads credentials on authentication failure. Reopen Codex only if the current MCP process remains unavailable.
6. **Will an authentication failure auto-retry generation?** No. Only one authentication refresh is allowed, and uncertain results are not replayed.

See [deep FAQ](references/faq-deep.md) for edge cases, compatibility, commercial, and compliance questions. See [usage examples](references/examples.md) for full interaction samples.

## Output accuracy

Report only `configured`, `missing`, the need to reconfigure, or a non-destructive validation result. Any operational state that cannot be confirmed must be labeled unverified. Never fabricate credential paths, Token status, tool inventories, or ProcessOn account capabilities.
