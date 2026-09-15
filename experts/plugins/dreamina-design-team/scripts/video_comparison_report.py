"""Self-contained, responsive source/design/output comparison report.

The report is the human-facing artifact of a video project. It embeds only
already-redacted JSON and local relative artifact names: never source or
generated media bytes, never an absolute private path, and never a credential,
transcript, or rights-evidence payload.
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ABSOLUTE_PATH_PATTERN = re.compile(r"(?:^|[\s\"'(=])(/(?:Users|home|private|var|tmp|Volumes)/[^\s\"'()]+)")
FORBIDDEN_KEYS = frozenset(
    {
        "source_path",
        "local_path",
        "transcript",
        "rights_evidence",
        "token",
        "api_key",
        "password",
        "secret",
        "authorization",
        "account_id",
        "thirdparty_id",
    }
)

REPORT_SECTIONS = (
    ("source_facts", "Source facts"),
    ("preserved_dimensions", "Preserved structural dimensions"),
    ("redesigned_content", "Redesigned expressive content"),
    ("shots", "Per-shot generation and evaluation"),
    ("audio_subtitles", "Audio and subtitle provenance"),
    ("final_media", "Final media gates"),
)


class ComparisonReportError(RuntimeError):
    """The report payload contains private data that must not be embedded."""


def _reject_private_fields(value: Any, path: str = "$") -> None:
    """Reject private field *names*.

    Absolute paths are handled differently: they are redacted rather than
    rejected, because a legitimate fact (for example a measured duration) may
    travel next to a path-shaped string that the report must still render.
    """
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise ComparisonReportError(f"report payload exposes a private field at {path}.{key}")
            _reject_private_fields(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_private_fields(item, f"{path}[{index}]")


def redact_for_embedding(value: Any) -> Any:
    """Recursively replace absolute paths with a placeholder before embedding."""
    if isinstance(value, Mapping):
        return {str(key): redact_for_embedding(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_for_embedding(item) for item in value]
    if isinstance(value, str):
        return ABSOLUTE_PATH_PATTERN.sub(lambda m: "<redacted-path>", value)
    return value


def _escape(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "&mdash;"
    if isinstance(value, (int, float)):
        return html.escape(str(value))
    if isinstance(value, (Mapping, list, tuple)):
        return html.escape(json.dumps(redact_for_embedding(value), sort_keys=True, ensure_ascii=False))
    return html.escape(str(redact_for_embedding(str(value))))


_STYLE = """
:root { color-scheme: light dark; --ink:#111827; --muted:#6b7280; --line:#e5e7eb; --bg:#ffffff; --card:#f9fafb; }
@media (prefers-color-scheme: dark) {
  :root { --ink:#e5e7eb; --muted:#9ca3af; --line:#374151; --bg:#0b0f19; --card:#111827; }
}
* { box-sizing: border-box; }
body { margin:0; padding:1rem; background:var(--bg); color:var(--ink);
  font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
header, section { max-width: 1180px; margin: 0 auto 1.25rem; }
h1 { font-size: 1.35rem; margin: 0 0 .25rem; }
h2 { font-size: 1.05rem; margin: 1.25rem 0 .5rem; padding-bottom:.35rem; border-bottom:1px solid var(--line); }
.meta { color: var(--muted); font-size: .85rem; }
.grid { display: grid; gap: .75rem; grid-template-columns: 1fr; }
.card { background: var(--card); border:1px solid var(--line); border-radius:.6rem; padding:.75rem; }
table { width:100%; border-collapse: collapse; font-size:.85rem; }
th, td { text-align:left; padding:.4rem .5rem; border-bottom:1px solid var(--line); vertical-align: top; }
th { color: var(--muted); font-weight:600; }
.pass { color:#047857; font-weight:600; }
.fail { color:#b91c1c; font-weight:600; }
.disclaimer { color: var(--muted); font-size:.8rem; border-left:3px solid var(--line); padding-left:.6rem; }
/* Small phone: 390x884 */
@media (max-width: 767px) {
  body { padding:.6rem; font-size:14px; }
  .grid { grid-template-columns: 1fr; }
  th, td { padding:.3rem .35rem; }
  table { display:block; overflow-x:auto; }
}
/* Tablet portrait: 768x1024 */
@media (min-width: 768px) {
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
/* Desktop: 1280x1024 */
@media (min-width: 1200px) {
  body { padding:1.5rem; }
  .grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  header, section { max-width: 1280px; }
}
@media print { body { background:#fff; color:#000; } .card { break-inside: avoid; } }
"""


class ComparisonReportService:
    """Render a self-contained HTML and JSON comparison report."""

    def render(self, payload: Mapping[str, Any]) -> str:
        _reject_private_fields(payload)
        project = payload.get("project") or {}
        title = str(project.get("title") or "Video project comparison")
        blocks = [
            "<!doctype html>",
            '<html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{html.escape(title)}</title>",
            f"<style>{_STYLE}</style>",
            "</head><body>",
            "<header>",
            f"<h1>{html.escape(title)}</h1>",
            f'<p class="meta">project {_escape(project.get("project_id"))} &middot; '
            f'composition {_escape(project.get("composition_version"))} &middot; '
            f'generated {_escape(payload.get("generated_at"))}</p>',
            "</header>",
        ]

        for key, heading in REPORT_SECTIONS:
            section = payload.get(key)
            if section is None:
                continue
            blocks.append("<section>")
            blocks.append(f"<h2>{html.escape(heading)}</h2>")
            blocks.append(self._render_section(section))
            blocks.append("</section>")

        blocks.append("<section>")
        blocks.append('<p class="disclaimer">Rights assertion: this report records the '
                      'assertion supplied for the project. It is not a legal opinion and '
                      'does not verify ownership of the source material.</p>')
        blocks.append("</section>")

        blocks.append('<section id="payload"><h2>Redacted payload</h2>')
        blocks.append(
            f'<pre class="card">{html.escape(json.dumps(redact_for_embedding(payload), indent=2, sort_keys=True, ensure_ascii=False))}</pre>'
        )
        blocks.append("</section>")
        blocks.append("</body></html>")
        return "\n".join(blocks)

    def _render_section(self, section: Any) -> str:
        if isinstance(section, Mapping) and "gates" in section:
            return self._render_gates(section["gates"])
        if isinstance(section, Mapping) and "rows" in section:
            return self._render_table(section["rows"])
        if isinstance(section, (list, tuple)):
            return self._render_table(section)
        if isinstance(section, Mapping):
            return self._render_table([{"field": k, "value": v} for k, v in section.items()])
        return f'<p class="card">{_escape(section)}</p>'

    def _render_table(self, rows: Any) -> str:
        if not isinstance(rows, (list, tuple)) or not rows:
            return '<p class="card">No entries.</p>'
        first = rows[0]
        if not isinstance(first, Mapping):
            return f'<p class="card">{_escape(rows)}</p>'
        columns = list(first.keys())
        head = "".join(f"<th>{html.escape(str(c))}</th>" for c in columns)
        body = []
        for row in rows:
            cells = []
            for column in columns:
                value = row.get(column) if isinstance(row, Mapping) else None
                css = ""
                if column == "passed":
                    css = ' class="pass"' if value else ' class="fail"'
                cells.append(f"<td{css}>{_escape(value)}</td>")
            body.append(f"<tr>{''.join(cells)}</tr>")
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"

    def _render_gates(self, gates: Any) -> str:
        if not isinstance(gates, Mapping):
            return '<p class="card">No gates.</p>'
        rows = [
            {"gate": name, "passed": bool((value or {}).get("passed")),
             "measured": (value or {}).get("measured"), "expected": (value or {}).get("expected")}
            for name, value in sorted(gates.items())
        ]
        return self._render_table(rows)

    def write(self, payload: Mapping[str, Any], html_path: Path, json_path: Path) -> dict[str, str]:
        """Write the HTML report and its machine-readable JSON sidecar."""
        html_document = self.render(payload)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_document, encoding="utf-8")
        json_path.write_text(
            json.dumps(redact_for_embedding(payload), indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )
        return {"html": str(html_path), "json": str(json_path)}


__all__ = [
    "ComparisonReportError",
    "ComparisonReportService",
    "redact_for_embedding",
]
