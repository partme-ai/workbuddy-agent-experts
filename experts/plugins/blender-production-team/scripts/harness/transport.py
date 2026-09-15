"""Authenticated local JSON-line transport for Harness sessions."""

from __future__ import annotations

import json
import os
import socket
import socketserver
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Endpoint:
    kind: str
    address: object


def choose_endpoint(platform: str, *, session_id: str, runtime_dir: str) -> Endpoint:
    safe_id = "".join(character for character in session_id if character.isalnum() or character in "-_")
    if platform == "win32":
        return Endpoint("pipe", rf"\\.\pipe\codex-blender-{safe_id}")
    if platform == "darwin":
        return Endpoint("unix", str(Path(runtime_dir) / f"codex-blender-{safe_id}.sock"))
    return Endpoint("tcp", ("127.0.0.1", 0))


class _ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = False
    daemon_threads = True


if hasattr(socketserver, "UnixStreamServer"):
    class _ThreadingUnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
        daemon_threads = True
else:
    _ThreadingUnixServer = None


class JsonLineServer:
    def __init__(self, endpoint: Endpoint, *, token: str, handle, max_request_bytes: int = 1024 * 1024):
        self.endpoint = endpoint
        self._token = token
        self._handle = handle
        self._max_request_bytes = max_request_bytes
        self._server = None
        self._thread = None
        self._pipe_listener = None
        self._closed = False

    def start(self) -> Endpoint:
        owner = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                raw = self.rfile.readline(owner._max_request_bytes + 1)
                if len(raw) > owner._max_request_bytes:
                    self._write({"error": {"code": "REQUEST_TOO_LARGE", "message": "request exceeds size limit"}})
                    return
                try:
                    envelope = json.loads(raw.decode("utf-8"))
                except Exception:
                    self._write({"error": {"code": "INVALID_JSON", "message": "request is not valid JSON"}})
                    return
                if envelope.get("token") != owner._token:
                    self._write({"error": {"code": "UNAUTHORIZED", "message": "invalid session token"}})
                    return
                try:
                    response = owner._handle(envelope.get("payload"))
                except Exception as exc:
                    response = {"error": {"code": getattr(exc, "code", "SERVER_ERROR"), "message": str(exc)}}
                self._write(response)

            def _write(self, payload):
                self.wfile.write(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")

        if self.endpoint.kind == "tcp":
            self._server = _ThreadingTCPServer(self.endpoint.address, Handler)
            host, port = self._server.server_address
            self.endpoint = Endpoint("tcp", (host, port))
        elif self.endpoint.kind == "unix":
            if _ThreadingUnixServer is None:
                raise RuntimeError("Unix domain sockets are unavailable on this platform")
            path = Path(str(self.endpoint.address))
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                raise RuntimeError(f"socket path already exists: {path}")
            self._server = _ThreadingUnixServer(str(path), Handler)
            os.chmod(path, 0o600)
        elif self.endpoint.kind == "pipe":
            from multiprocessing.connection import Listener
            self._pipe_listener = Listener(str(self.endpoint.address), family="AF_PIPE", authkey=self._token.encode("utf-8"))
            self._thread = threading.Thread(target=self._serve_pipe, name="codex-blender-pipe", daemon=True)
            self._thread.start()
            return self.endpoint
        else:
            raise ValueError(f"unknown transport kind: {self.endpoint.kind}")
        self._thread = threading.Thread(target=self._server.serve_forever, name="codex-blender-transport", daemon=True)
        self._thread.start()
        return self.endpoint

    def close(self) -> None:
        self._closed = True
        if self._pipe_listener is not None:
            self._pipe_listener.close()
            if self._thread:
                self._thread.join(timeout=2)
            self._pipe_listener = None
            return
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        if self.endpoint.kind == "unix":
            try:
                Path(str(self.endpoint.address)).unlink()
            except FileNotFoundError:
                pass
        self._server = None

    def _serve_pipe(self) -> None:
        while not self._closed and self._pipe_listener is not None:
            try:
                connection = self._pipe_listener.accept()
            except (OSError, EOFError):
                break
            try:
                raw = connection.recv_bytes(self._max_request_bytes + 1)
                if len(raw) > self._max_request_bytes:
                    response = {"error": {"code": "REQUEST_TOO_LARGE", "message": "request exceeds size limit"}}
                else:
                    envelope = json.loads(raw.decode("utf-8"))
                    if envelope.get("token") != self._token:
                        response = {"error": {"code": "UNAUTHORIZED", "message": "invalid session token"}}
                    else:
                        response = self._handle(envelope.get("payload"))
                connection.send_bytes(json.dumps(response, separators=(",", ":")).encode("utf-8"))
            except Exception as exc:
                try:
                    connection.send_bytes(json.dumps({"error": {"code": getattr(exc, "code", "SERVER_ERROR"), "message": str(exc)}}).encode("utf-8"))
                except Exception:
                    pass
            finally:
                connection.close()


def send_request(endpoint: Endpoint, token: str, payload: dict, *, timeout: float = 5.0) -> dict:
    envelope = json.dumps({"token": token, "payload": payload}, separators=(",", ":")).encode("utf-8") + b"\n"
    if endpoint.kind == "tcp":
        sock = socket.create_connection(endpoint.address, timeout=timeout)
    elif endpoint.kind == "unix":
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(str(endpoint.address))
    elif endpoint.kind == "pipe":
        from multiprocessing.connection import Client
        connection = Client(str(endpoint.address), family="AF_PIPE", authkey=token.encode("utf-8"))
        try:
            connection.send_bytes(envelope.rstrip(b"\n"))
            return json.loads(connection.recv_bytes().decode("utf-8"))
        finally:
            connection.close()
    else:
        raise ValueError(f"unknown transport kind: {endpoint.kind}")
    try:
        sock.sendall(envelope)
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
        return json.loads(b"".join(chunks).split(b"\n", 1)[0].decode("utf-8"))
    finally:
        sock.close()
