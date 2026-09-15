# Usage examples

## Example 1: First use

- Input: "First time using ProcessOn, please draw an architecture diagram for me."
- Decision: run the safe availability check first; when it returns missing, open the local setup page.
- Output: "Please finish the three-step setup on the page that just opened. Paste the Token only into the password field; once it is saved, reopen Codex and I will continue with the original architecture diagram request."

## Example 2: Invalid credential

- Input: the proxy returns `PROCESSON_AUTH_REQUIRED`.
- Decision: stop the generation call, enter the rotation flow, and do not repeat the upstream response.
- Output: "The ProcessOn credential is invalid or expired. I have opened the local update page; after saving the new Token and reopening Codex, I will continue with this diagram."

## Example 3: Configured but service temporarily unavailable

- Input: `check` returns configured, but `tools/list` is temporarily failing.
- Decision: distinguish credential presence from upstream reachability, and do not replay the generation.
- Output: "The local credential is configured; ProcessOn reachability is not verified at the moment. No generation request was issued or repeated, you can retry a read-only check later."
