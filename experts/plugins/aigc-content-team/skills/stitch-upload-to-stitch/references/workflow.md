# Upload to Stitch workflow

## Choose the transport

- `.png`, `.jpg`, `.jpeg`, `.webp`, `.html`, `.htm`: use the bundled private REST helper.
- `.md`: read and encode in-process, then use MCP `upload_design_md` with `projectId` and `designMdBase64`.
- Any other extension: reject before reading credentials or sending a request.

## Credentials and origin

The helper calls `platform_secret_provider()`, which checks the current process and then the restricted user configuration. It has no credential argument and no endpoint argument. Production requests are pinned to `https://stitch.googleapis.com`; an injected loopback transport exists only for offline tests.

## Run the local helper

```bash
python3 <SKILL_DIR>/scripts/upload_to_stitch.py \
  --project-id <PROJECT_ID> \
  --file-path <PATH_TO_HTML_OR_IMAGE> \
  --title /orders \
  --generated-by stitch-extract-static-html
```

The helper does not follow redirects and never retries a write automatically. It accepts only the current response shape `results[].screen`, validates each screen name belongs to the requested project, drops extra fields, and prints only safe names.

## Reconciliation

Use `get_project` with `name: projects/{project}`, `list_screens` with the bare project ID, and `get_screen` with `name: projects/{project}/screens/{screen}`. An empty, malformed, timed-out, or rejected response is an unknown write outcome; reconcile before proposing another write.

## Options

- `--project-id`: required bare numeric project ID.
- `--file-path`: required HTML or image path.
- `--title`: optional screen title.
- `--generated-by`: optional producer name for HTML.
