#!/usr/bin/env python3
"""Configure and check the current user's ProcessOn credential."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
import threading
import webbrowser
from collections.abc import Callable, Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from processon_harness.secrets import (
    CredentialError,
    TOKEN_KEY,
    UserConfigSecretProvider,
    platform_secret_provider,
)


SETUP_ASSETS = ROOT / "assets" / "setup"
MAX_BODY_SIZE = 8192
UI_TIMEOUT_SECONDS = 600


def build_parser() -> argparse.ArgumentParser:
    """Build the supported setup command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("ui", help="open the secure local setup page")
    commands.add_parser("setup", help="save a token using a hidden terminal prompt")
    commands.add_parser("check", help="report credential availability only")
    cli = commands.add_parser("cli", help="run the local ProcessOn MCP proxy")
    cli.add_argument("arguments", nargs=argparse.REMAINDER)
    run = commands.add_parser("run", help="run a command with the ProcessOn token")
    run.add_argument("arguments", nargs=argparse.REMAINDER)
    return parser


def credential_status(provider: object) -> dict[str, bool]:
    """Return availability without returning credential material."""
    try:
        return {"configured": provider.get_token() is not None}
    except CredentialError:
        return {"configured": False}


class _SetupHandler(BaseHTTPRequestHandler):
    server_version = "ProcessOnSetup"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        return None

    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'",
        )

    def _respond(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self._respond(status, "application/json; charset=utf-8", body)

    def do_GET(self) -> None:
        files = {
            "/styles.css": ("text/css; charset=utf-8", "styles.css"),
            "/app.js": ("text/javascript; charset=utf-8", "app.js"),
            "/logo.png": ("image/png", "../logo.png"),
            "/logo-light.png": ("image/png", "../logo-light.png"),
        }
        if self.path in {"/", "/index.html"}:
            text = (SETUP_ASSETS / "index.html").read_text(encoding="utf-8")
            text = text.replace("__CSRF_TOKEN__", self.server.csrf_token)
            self._respond(200, "text/html; charset=utf-8", text.encode("utf-8"))
            return
        if self.path in files:
            content_type, relative = files[self.path]
            self._respond(200, content_type, (SETUP_ASSETS / relative).read_bytes())
            return
        self._json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        if self.path not in {"/api/credentials", "/api/launch"}:
            self._json(404, {"ok": False, "error": "Not found"})
            return
        if self.headers.get("Origin") != self.server.expected_origin:
            self._json(403, {"ok": False, "error": "Request origin rejected"})
            return
        if self.headers.get("X-CSRF-Token") != self.server.csrf_token:
            self._json(403, {"ok": False, "error": "Request token rejected"})
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if content_type != "application/json":
            self._json(415, {"ok": False, "error": "JSON required"})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 1 or length > MAX_BODY_SIZE:
            self._json(400, {"ok": False, "error": "Invalid request size"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise CredentialError("Invalid request input")
            if self.path == "/api/credentials":
                token = payload.get("token")
                if not isinstance(token, str):
                    raise CredentialError("Invalid token input")
                self.server.provider.save_token(token)
        except (CredentialError, UnicodeError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "Token could not be saved"})
            return
        if self.path == "/api/launch":
            launched = self.server.launch_codex()
            payload = {"ok": True} if launched else {"ok": False, "error": "Codex could not be opened"}
            self._json(200 if launched else 500, payload)
            return
        self._json(200, {"ok": True})


def create_setup_server(
    provider: UserConfigSecretProvider,
    launch_codex: Callable[[], bool] | None = None,
) -> tuple[ThreadingHTTPServer, str]:
    """Create a loopback-only setup server on an ephemeral port."""
    import secrets

    server = ThreadingHTTPServer(("127.0.0.1", 0), _SetupHandler)
    host, port = server.server_address
    server.provider = provider
    server.launch_codex = _launch_codex if launch_codex is None else launch_codex
    server.csrf_token = secrets.token_urlsafe(32)
    server.expected_origin = f"http://{host}:{port}"
    return server, f"{server.expected_origin}/"


def _launch_codex() -> bool:
    """Open Codex without waiting for the desktop process to exit."""
    commands = (
        ["open", "-a", "Codex"] if sys.platform == "darwin" else None,
        ["cmd", "/c", "start", "", "codex"] if os.name == "nt" else None,
        ["codex"] if os.name != "nt" else None,
    )
    for command in commands:
        if command is None:
            continue
        try:
            subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except OSError:
            continue
    return False


def run_ui(
    provider: UserConfigSecretProvider,
    open_browser: Callable[[str], bool] = webbrowser.open,
) -> int:
    """Open and serve the setup page for a bounded period."""
    server, url = create_setup_server(provider)
    timer = threading.Timer(UI_TIMEOUT_SECONDS, server.shutdown)
    timer.daemon = True
    timer.start()
    try:
        open_browser(url)
        server.serve_forever()
    except KeyboardInterrupt:
        return 130
    finally:
        timer.cancel()
        server.server_close()
    return 0


def run_hidden_setup(
    provider: UserConfigSecretProvider,
    prompt: Callable[[str], str] = getpass.getpass,
) -> int:
    """Save a token read from a hidden terminal prompt."""
    try:
        provider.save_token(prompt("ProcessOn Token: "))
    except CredentialError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("ProcessOn credential saved. Reopen Codex to continue.")
    return 0


def _run_with_token(arguments: list[str]) -> int:
    if arguments and arguments[0] == "--":
        arguments = arguments[1:]
    if not arguments:
        print("A command is required", file=sys.stderr)
        return 2
    token = platform_secret_provider().get_token()
    if token is None:
        print("ProcessOn credential: missing", file=sys.stderr)
        return 2
    environment = os.environ.copy()
    environment[TOKEN_KEY] = token
    return subprocess.run(arguments, env=environment, check=False).returncode


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    saved_provider = UserConfigSecretProvider()
    if args.command == "ui":
        return run_ui(saved_provider)
    if args.command == "setup":
        return run_hidden_setup(saved_provider)
    if args.command == "check":
        status = credential_status(platform_secret_provider())
        state = "configured" if status["configured"] else "missing"
        print(f"ProcessOn credential: {state}")
        return 0 if status["configured"] else 2
    if args.command == "cli":
        command = [sys.executable, str(ROOT / "scripts" / "processon_mcp_proxy.py")]
        return subprocess.run(command + args.arguments, check=False).returncode
    return _run_with_token(args.arguments)


if __name__ == "__main__":
    raise SystemExit(main())
