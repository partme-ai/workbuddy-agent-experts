# Deep FAQ

1. **Will a corporate proxy affect the setup page?** No. The setup page only uses loopback; the proxy policy for reaching ProcessOn is handled by the environment that runs Codex.
2. **Can multiple system accounts share a credential?** They should not. Each system user has their own restricted config.
3. **Can a team submit a shared Token?** Not recommended and not supported by this Skill; use an organization-approved credential governance approach.
4. **Can we switch to the system keychain?** Not implemented in the current version; that is a future optional migration and must not be claimed as supported.
5. **The browser is blocked by policy — what now?** Use the hidden terminal input from `processon_setup.py setup`.
6. **The Token already has a `Bearer` prefix — is that okay?** Yes; the setup strips one prefix on save and the proxy adds it back when sending.
7. **ProcessOn reports the Token as invalid at the business layer — what now?** Treat it as an authentication failure, open the setup page for rotation, and do not echo the original response.
8. **Does the plugin license cover commercial use?** No; the plugin license does not replace ProcessOn's terms of service, plan limits, or content compliance requirements.
9. **How do we run this in CI?** Provide a raw `PROCESSON_MCP_TOKEN` inside a controlled child process; never commit it to the repository or build logs.
10. **How do we confirm an upgrade did not lose the credential?** After the upgrade, run `check`, then `initialize` and `tools/list`; do not probe with a generation request.
