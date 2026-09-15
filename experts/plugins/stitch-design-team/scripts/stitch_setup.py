#!/usr/bin/env python3
"""Configure and inject STITCH_API_KEY without modifying shell profiles."""

from __future__ import annotations

import getpass
import json
import secrets
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from stitch_harness.secrets import (  # noqa: E402
    SecretProvider,
    SecretStoreError,
    default_config_path,
    platform_secret_provider,
)


SETUP_ASSETS = PLUGIN_ROOT / "assets" / "setup"


def config_path() -> Path:
    return default_config_path()


def save_key(key: str, provider: SecretProvider | None = None) -> None:
    value = key.strip()
    if not value:
        raise ValueError("STITCH_API_KEY cannot be empty")
    target = provider or platform_secret_provider()
    target.set(value)
    stored = target.get()
    if stored != value:
        raise SecretStoreError("credential store verification failed")


def load_key(provider: SecretProvider | None = None) -> str | None:
    return (provider or platform_secret_provider()).get()


def setup(secret_provider: SecretProvider | None = None) -> int:
    print("Create a Stitch API key at https://stitch.withgoogle.com/settings")
    print("Paste it only into the hidden prompt below; never paste it into chat.")
    key = getpass.getpass("Stitch API key (hidden): ")
    try:
        save_key(key, secret_provider)
    except (SecretStoreError, ValueError) as error:
        print(f"Could not save Stitch credentials: {error}", file=sys.stderr)
        return 1
    print("Saved Stitch credentials to the current user's configuration.")
    print("Run this setup command again to replace the saved key.")
    return 0


def check(secret_provider: SecretProvider | None = None) -> int:
    try:
        available = load_key(secret_provider)
    except SecretStoreError as error:
        print(f"Stitch credential check failed: {error}", file=sys.stderr)
        return 1
    if not available:
        print("STITCH_API_KEY is not configured")
        return 1
    print("STITCH_API_KEY is available through the configured secret provider")
    if (PLUGIN_ROOT / ".mcp.json").is_file():
        print("Stitch MCP configuration is present")
        return 0
    print("Stitch MCP configuration is missing")
    return 1


def command_environment(secret_provider: SecretProvider | None = None) -> dict[str, str] | None:
    try:
        key = load_key(secret_provider)
    except SecretStoreError as error:
        print(f"Could not read Stitch credentials: {error}", file=sys.stderr)
        return None
    if not key:
        print("STITCH_API_KEY is not configured. Run the setup command first.", file=sys.stderr)
        return None
    environment = os.environ.copy()
    environment["STITCH_API_KEY"] = key
    return environment


def launch_command(arguments: list[str], *, wait: bool) -> int:
    if arguments and arguments[0] == "--":
        arguments = arguments[1:]
    if not arguments:
        print("No command was provided.", file=sys.stderr)
        return 2
    environment = command_environment()
    if environment is None:
        return 1
    executable = shutil.which(arguments[0], path=environment.get("PATH"))
    if executable is None:
        print(f"Command not found: {arguments[0]}", file=sys.stderr)
        return 1
    command = [executable, *arguments[1:]]
    if wait:
        return subprocess.call(command, env=environment)
    subprocess.Popen(command, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return 0


def run_command(arguments: list[str]) -> int:
    return launch_command(arguments, wait=True)


def desktop() -> int:
    if sys.platform == "darwin":
        executable = Path("/Applications/ChatGPT.app/Contents/MacOS/ChatGPT")
        if not executable.is_file():
            print("ChatGPT was not found in /Applications.", file=sys.stderr)
            return 1
        environment = command_environment()
        if environment is None:
            return 1
        subprocess.Popen(
            [str(executable)],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print("ChatGPT started with STITCH_API_KEY in its process environment.")
        return 0
    print("Use 'run -- <desktop executable>' for this platform.", file=sys.stderr)
    return 1


def create_setup_server(
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    secret_provider: SecretProvider | None = None,
):
    state = SimpleNamespace(csrf_token=secrets.token_urlsafe(32), completed=False)
    target_provider = secret_provider or platform_secret_provider()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def headers_common(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'")

        def send_content(self, status, content, content_type):
            self.send_response(status)
            self.headers_common()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            files = {
                "/": ("index.html", "text/html; charset=utf-8", SETUP_ASSETS),
                "/styles.css": ("styles.css", "text/css; charset=utf-8", SETUP_ASSETS),
                "/title.css": ("title.css", "text/css; charset=utf-8", SETUP_ASSETS),
                "/app.js": ("app.js", "text/javascript; charset=utf-8", SETUP_ASSETS),
                "/logo.png": ("logo.png", "image/png", PLUGIN_ROOT / "assets"),
            }
            if self.path not in files:
                self.send_content(404, b'{"ok":false}', "application/json")
                return
            name, content_type, directory = files[self.path]
            content = (directory / name).read_bytes()
            if name == "index.html":
                content = content.replace(b"__CSRF_TOKEN__", state.csrf_token.encode())
            self.send_content(200, content, content_type)

        def do_POST(self):
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if self.headers.get("Origin") != origin:
                self.send_content(403, b'{"ok":false}', "application/json")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length < 1 or length > 8192 or self.headers.get_content_type() != "application/json":
                self.send_content(400, b'{"ok":false}', "application/json")
                return
            try:
                data = json.loads(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.send_content(400, b'{"ok":false}', "application/json")
                return
            if not secrets.compare_digest(str(data.get("csrfToken", "")), state.csrf_token):
                self.send_content(403, b'{"ok":false}', "application/json")
                return
            if self.path == "/api/save":
                try:
                    save_key(str(data.get("apiKey", "")), target_provider)
                except (SecretStoreError, ValueError):
                    self.send_content(400, b'{"ok":false,"message":"Key could not be saved"}', "application/json")
                    return
                state.completed = True
                self.send_content(200, b'{"ok":true}', "application/json")
                return
            if self.path == "/api/launch":
                code = launch_command(["codex"], wait=False)
                self.send_content(200 if code == 0 else 500, json.dumps({"ok": code == 0}).encode(), "application/json")
                return
            self.send_content(404, b'{"ok":false}', "application/json")

    server = ThreadingHTTPServer((host, port), Handler)
    return server, state


def run_ui() -> int:
    server, _state = create_setup_server()
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"Opening Stitch Design setup at {url}")
    webbrowser.open(url)
    timer = threading.Timer(600, server.shutdown)
    timer.daemon = True
    timer.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        timer.cancel()
        server.server_close()
    return 0


def usage() -> None:
    print(
        "Usage: stitch_setup.py ui | setup | check | cli [args...] | "
        "run -- <command> [args...] | desktop",
        file=sys.stderr,
    )


def main(arguments: list[str]) -> int:
    if not arguments:
        usage()
        return 2
    command, *rest = arguments
    if command == "setup":
        return setup()
    if command == "check":
        return check()
    if command == "cli":
        if rest and rest[0] == "--":
            rest = rest[1:]
        return run_command(["codex", *rest])
    if command == "run":
        return run_command(rest)
    if command == "desktop":
        return desktop()
    if command == "ui":
        return run_ui()
    usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
