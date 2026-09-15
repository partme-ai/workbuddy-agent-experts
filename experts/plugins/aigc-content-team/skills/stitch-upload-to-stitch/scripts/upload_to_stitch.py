#!/usr/bin/env python3
r"""Upload an image or HTML file to a Stitch project via BatchCreateScreens.

WHY THIS SCRIPT EXISTS:
    The AI model cannot upload files via the MCP tool directly because MCP tool
    call arguments are part of the model's *output*. The model must re-emit the
    entire base64-encoded file as generated text, but its output token limit
    (~16K tokens) is far smaller than a typical file's base64 encoding (e.g.
    a 53KB PNG becomes ~71K chars of base64). The output gets truncated
    mid-string, producing a corrupted payload that the API rejects.

    This script bypasses the model entirely — it reads the file, encodes it
    in-process, and sends the full payload directly over HTTP with no token
    limits.

SUPPORTED FILE TYPES:
    - Images: .png, .jpg, .jpeg, .webp
    - HTML: .html, .htm
    Markdown uses the MCP ``upload_design_md`` tool instead of this private REST helper.

Usage:
    python3 upload_to_stitch.py \
        --project-id <PROJECT_ID> \
        --file-path <PATH_TO_FILE> \
        [--title <SCREEN_TITLE>] \
        [--generated-by <GENERATED_BY>]

Credentials come from the plugin's environment-first user configuration chain.
"""

import argparse
import base64
import json
import pathlib
import re
import sys
from typing import Any
import urllib.request
import urllib.parse
import urllib.error

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
  sys.path.insert(0, str(PLUGIN_ROOT))

from stitch_harness.secrets import SecretStoreError, platform_secret_provider

try:
  import ssl
  import certifi
  _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
  _SSL_CONTEXT = None


# Maps file extensions to MIME types.
_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".html": "text/html",
    ".htm": "text/html",
}

_GOOGLE_UPLOAD_ORIGIN = "https://stitch.googleapis.com"


class NoRedirect(urllib.request.HTTPRedirectHandler):
  """Never forward upload credentials or repeat a POST after a redirect."""

  def redirect_request(self, req, fp, code, msg, headers, newurl):
    return None


def secure_urlopen(req, *, timeout=120, context=None):
  """Use verified TLS and disable redirects; no automatic write retries."""
  return urllib.request.build_opener(
      NoRedirect(), urllib.request.HTTPSHandler(context=context)
  ).open(req, timeout=timeout)


def encode_file(path: pathlib.Path) -> str:
  """Read and base64-encode a file."""
  with open(path, "rb") as f:
    return base64.b64encode(f.read()).decode("utf-8")


def validated_result_summary(result: Any, project_id: str) -> dict[str, Any]:
  """Accept only identifiers in the requested project; reject ambiguous results.

  This is a conservative local acceptance contract, not a claim that every
  future server identifier shape is known. Unrecognized shapes require reads
  to reconcile the upload instead of reporting success or logging raw values.
  """
  unknown = "上传结果未知：响应标识缺失或结构异常，请先对账，勿重复提交。"
  if not isinstance(result, dict):
    raise ValueError(unknown)
  results = result.get("results")
  if not isinstance(results, list) or not results:
    raise ValueError(unknown)
  # Current pinned tool-schema examples use 32-character hexadecimal IDs.
  # A different server format is an unknown outcome, never a reason to print it.
  resource_pattern = re.compile(r"projects/" + re.escape(project_id) + r"/screens/[A-Fa-f0-9]{32}")
  screen_names = set()
  safe_screens = []
  for item in results:
    screen = item.get("screen") if isinstance(item, dict) else None
    name = screen.get("name") if isinstance(screen, dict) else None
    if not isinstance(name, str) or not resource_pattern.fullmatch(name) or name in screen_names:
      raise ValueError(unknown)
    screen_names.add(name)
    safe_screens.append({"name": name})
  return {"screens": safe_screens}


def call_batch_create_screens(
    api_url: str,
    api_key: str,
    project_id: str,
    requests: list[dict[str, Any]],
    create_screen_instances: bool = False,
    urlopen: Any = secure_urlopen,
) -> dict[str, Any]:
  """Call BatchCreateScreens REST API directly.

  Endpoint: POST /v1/{parent=projects/*}/screens:batchCreate

  Args:
    api_url: Base URL of the Stitch API (e.g. https://stitch.googleapis.com).
    api_key: API key for authentication.
    project_id: The Stitch project ID.
    requests: List of CreateScreenRequest dicts, each containing a screen.
    create_screen_instances: Whether to create screen instances for display.
    urlopen: The urlopen function to use (for testing).

  Returns:
    Validated identifier-only summary. Unexpected shapes fail closed without
    logging response data; no automatic retry occurs.
  """
  endpoint = urllib.parse.urlsplit(api_url)
  loopback_test_origin = (
      urlopen is not secure_urlopen
      and endpoint.scheme == "http"
      and endpoint.hostname in {"127.0.0.1", "localhost", "::1"}
      and endpoint.port is not None
      and not endpoint.username
      and not endpoint.password
      and not endpoint.query
      and not endpoint.fragment
      and endpoint.path in {"", "/"}
  )
  if api_url.rstrip("/") != _GOOGLE_UPLOAD_ORIGIN and not loopback_test_origin:
    raise ValueError("生产上传地址必须是 https://stitch.googleapis.com；仅测试可注入 loopback transport。")
  if not project_id.isascii() or not project_id.isdigit():
    raise ValueError("缺少有效项目 ID：请从 Stitch 元数据获取纯数字字符串。")
  url = f"{api_url.rstrip('/')}/v1/projects/{project_id}/screens:batchCreate"

  payload = {
      "parent": f"projects/{project_id}",
      "requests": requests,
      "createScreenInstances": create_screen_instances,
  }

  data = json.dumps(payload).encode("utf-8")
  req = urllib.request.Request(
      url,
      data=data,
      headers={
          "Content-Type": "application/json",
          "X-Goog-Api-Key": api_key,
      },
      method="POST",
  )

  try:
    urlopen_kwargs = {"timeout": 120}
    if _SSL_CONTEXT is not None:
      urlopen_kwargs["context"] = _SSL_CONTEXT
    with urlopen(req, **urlopen_kwargs) as resp:
      body = resp.read().decode("utf-8")
      if not body:
        raise ValueError("上传结果未知：响应为空，请先对账，勿重复提交。")
      try:
        result = json.loads(body)
      except json.JSONDecodeError:
        raise ValueError("上传结果未知：响应不是有效 JSON，请先对账，勿重复提交。") from None
      return validated_result_summary(result, project_id)
  except urllib.error.HTTPError as e:
    raise ValueError(f"上传返回 HTTP {e.code}；请检查授权并读取项目状态，勿重复提交。") from None


def build_screen_request(
    mime_type: str,
    b64_data: str,
    title: str | None = None,
    generated_by: str | None = None,
) -> dict[str, Any]:
  """Build a CreateScreenRequest dict from a file.

  For images, the file is set as the screenshot.
  For HTML, the file is set as the html_code.

  Args:
    mime_type: The MIME type of the file.
    b64_data: Base64-encoded file content.
    title: Optional title for the screen.
    generated_by: Optional value for the generatedBy field (HTML only).

  Returns:
    A CreateScreenRequest-shaped dict.
  """
  file_obj = {
      "fileContentBase64": b64_data,
      "mimeType": mime_type,
  }

  if mime_type == "text/html":
    screen = {
        "htmlCode": file_obj,
        "screenType": "DOCUMENT",
        "isCreatedByClient": True,
    }
    if not generated_by:
      generated_by = "UserUploadedHtml"
    if generated_by:
      screen["generatedBy"] = generated_by
  else:
    screen = {
        "screenshot": file_obj,
        "screenType": "IMAGE",
        "isCreatedByClient": True,
    }

  if title:
    screen["title"] = title

  return {"screen": screen}


def parse_args():
  """Parse command-line arguments."""
  parser = argparse.ArgumentParser(
      description="Upload a file to a Stitch project via BatchCreateScreens."
  )
  parser.add_argument("--project-id", required=True, help="Stitch project ID")
  parser.add_argument(
      "--file-path",
      required=True,
      type=pathlib.Path,
      help=(
          "Path to the file to upload. Supported types:"
          f" {', '.join(sorted(_MIME_TYPES.keys()))}"
      ),
  )
  parser.add_argument(
      "--title",
      default=None,
      help="Optional title for the created screen",
  )
  parser.add_argument(
      "--generated-by",
      default=None,
      help=(
          "Value for the generatedBy field in the screen proto"
          " (HTML uploads only)."
      ),
  )
  args = parser.parse_args()
  try:
    args.api_key = platform_secret_provider().get()
  except SecretStoreError as error:
    parser.error(f"无法读取 Stitch 凭据配置：{error}")
  if not args.api_key:
    parser.error("缺少 Stitch 凭据：请先运行 scripts/stitch_setup.py setup，勿粘贴密钥到会话。")
  return args


def main():
  args = parse_args()

  file_path = args.file_path
  file_suffix = file_path.suffix.lower()
  mime_type = _MIME_TYPES.get(file_suffix)

  if mime_type is None:
    print(
        f"Error: Unsupported file type '{file_suffix}'. Supported types:"
        f" {', '.join(sorted(_MIME_TYPES.keys()))}"
    )
    sys.exit(1)

  if not file_path.is_file():
    print(f"Error: File not found: {file_path}")
    sys.exit(1)

  if args.generated_by and mime_type != "text/html":
    print("Warning: --generated-by is ignored for image uploads.")

  print(f"File:      {file_path}")
  print(f"MIME type: {mime_type}")

  b64_data = encode_file(file_path)
  print(f"Base64:    {len(b64_data)} chars")

  screen_request = build_screen_request(
      mime_type, b64_data, title=args.title, generated_by=args.generated_by,
  )

  print(f"\nUploading to project: {args.project_id}")

  result = call_batch_create_screens(
      api_url=_GOOGLE_UPLOAD_ORIGIN,
      api_key=args.api_key,
      project_id=args.project_id,
      requests=[screen_request],
      create_screen_instances=True,
  )

  # The transport boundary has validated structure, types and identifier syntax.
  print(json.dumps(result, indent=2))


if __name__ == "__main__":
  try:
    main()
  except (OSError, ValueError, urllib.error.URLError):
    print("上传结果未知或尚未开始：请检查输入文件、HTTPS/CA 与授权；若已发送请求，先对账，不要直接重试。", file=sys.stderr)
    sys.exit(1)
