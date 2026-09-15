---
name: processon-diagram-generator
license: Apache-2.0
description: Generate ProcessOn-compatible editable diagrams and optionally render images through the ProcessOn API. Use when the user explicitly requests ProcessOn, hosted editable diagram output, or API-rendered flowcharts, swimlanes, sequences, architectures, ER diagrams, org charts, timelines, or infographics. Requires PROCESSON_API_KEY for remote generation. Prefer Mermaid for ordinary Markdown-native diagrams and PlantUML for strict UML/C4 source.
---

# ProcessOn Diagram Generator

Convert an evidence-backed diagram specification into editable DSL and, when requested, a rendered image.

## Routing

- Use this skill only when ProcessOn or hosted editable output is requested.
- Use the **`mermaid`** skill for ordinary Markdown-native diagrams. Install with: `npx skills add full-stack-skills/document-skills --skill mermaid`.
- Use the **`plantuml`** skill for strict UML, C4, or `.puml` output. Install with: `npx skills add full-stack-skills/document-skills --skill plantuml`.
- Use the **`processon-mindmap`** skill when only a ProcessOn-ready mind-map outline is needed. Install with: `npx skills add full-stack-skills/document-skills --skill processon-mindmap`.

## Configuration

Required:

```bash
export PROCESSON_API_KEY="<your-processon-api-key>"
```

Obtain a key at `https://smart.processon.com/user`. Never print, persist, or include the key in prompts or output.

Optional configuration:

| Variable | Purpose |
|---|---|
| `PROCESSON_DSL_API_URL` | Override the DSL API URL |
| `PROCESSON_RENDER_API_URL` | Override the image-render API URL |
| `PROCESSON_MODEL` | Override the remote model |
| `PROCESSON_UID` | Override the request UID |
| `PROCESSON_CONNECT_TIMEOUT` | Request timeout in seconds |
| `PROCESSON_MAX_RETRIES` | Retries for timeout, 429, and 5xx failures |

Do not perform a remote update check on every invocation. Check the bundled version files only when the user asks about updates or maintenance.

Run an explicit update check only on request:

```bash
python3 scripts/check_update.py
```

## Workflow

1. Extract nodes, relationships, decisions, participants, states, and labels from the request or inspected source.
2. Resolve missing relationships with source inspection; ask only when ambiguity materially changes the diagram.
3. Build a concise prompt that preserves the user's language and requests a readable layout with minimal crossings.
4. Run the bundled client:

```bash
python3 scripts/processon_api_client.py \
  --title "登录流程" \
  "生成登录、鉴权、数据查询和令牌签发流程图"
```

5. Use `--no-render` when only editable DSL is needed.
6. Deliver the complete DSL and edit URL even if image rendering fails.

## Output contract

The final response must include:

- complete DSL without truncation;
- the edit URL `https://smart.processon.com/editor`;
- rendered image URL or saved path when rendering succeeds;
- a clear rendering failure reason when it fails;
- assumptions made while reconstructing the diagram.

Use ordinary Markdown links or local image previews when supported by the host. Do not impose raw-URL-only formatting unless the user requests it.

## Reliability rules

- Retry only timeouts, connection failures, HTTP 429, and HTTP 5xx.
- Use bounded exponential backoff.
- Do not retry authentication or other deterministic 4xx failures.
- Keep DSL delivery independent from image rendering success.
- Save images beneath the requested project or explicit output directory; never use a machine-specific hard-coded path.
- Reject empty or malformed API responses with a diagnostic that does not expose credentials.

## Validation

Before completion, confirm the DSL is non-empty, the diagram type is known or explicitly generic, the edit URL is present, and any local output path exists. Run the offline unit tests after changing the client:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```
