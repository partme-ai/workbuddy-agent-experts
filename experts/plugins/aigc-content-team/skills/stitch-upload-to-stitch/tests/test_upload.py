"""Offline upload contract tests; no HTTP request reaches the network."""
import contextlib
import importlib.util
import io
import json
import os
import runpy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("upload", Path(__file__).parents[1] / "scripts/upload_to_stitch.py")
upload = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(upload)


class Response(io.BytesIO):
    def getcode(self):
        return 200


class UploadTests(unittest.TestCase):
    def test_cli_has_no_api_key_or_api_url_surface(self):
        with patch("sys.argv", ["upload", "--project-id", "123", "--file-path", "demo.html", "--api-key", "leaked"]), \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                upload.parse_args()
        with patch("sys.argv", ["upload", "--project-id", "123", "--file-path", "demo.html", "--api-url", "https://example.invalid"]), \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                upload.parse_args()

    def test_key_comes_from_platform_secret_provider(self):
        provider = unittest.mock.Mock()
        provider.get.return_value = "config-secret"
        with patch.object(upload, "platform_secret_provider", return_value=provider), \
             patch("sys.argv", ["upload", "--project-id", "123", "--file-path", "demo.html"]):
            self.assertEqual(upload.parse_args().api_key, "config-secret")

    def test_reject_insecure_endpoint_before_transport(self):
        called = []
        with self.assertRaises(ValueError):
            upload.call_batch_create_screens("http://example.invalid", "test", "123", [], urlopen=lambda *a, **k: called.append(a))
        self.assertEqual(called, [])

    def test_reject_non_google_https_origin_before_transport(self):
        called = []
        with self.assertRaisesRegex(ValueError, "stitch.googleapis.com"):
            upload.call_batch_create_screens(
                "https://example.invalid", "test", "123", [],
                urlopen=lambda *a, **k: called.append(a),
            )
        self.assertEqual(called, [])

    def test_injected_loopback_origin_is_available_only_for_tests(self):
        response = {"results": [{"screen": {"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}]}
        result = upload.call_batch_create_screens(
            "http://127.0.0.1:8765", "test", "123", [],
            urlopen=lambda *a, **k: Response(json.dumps(response).encode()),
        )
        self.assertEqual(result["screens"][0]["name"], "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    def test_request_and_no_payload_logging(self):
        captured = []
        def transport(req, **kwargs):
            captured.append((req, kwargs))
            return Response(json.dumps({"results": [{"screen": {"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "privateNote": "PRIVATE_CONTENT"}}]}).encode())
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = upload.call_batch_create_screens("https://stitch.googleapis.com", "offline-test-key", "123", [], urlopen=transport)
        self.assertEqual(result["screens"][0]["name"], "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        self.assertNotIn("PRIVATE_CONTENT", stdout.getvalue())
        self.assertNotIn("offline-test-key", stdout.getvalue())
        self.assertEqual(captured[0][0].method, "POST")
        self.assertEqual(captured[0][1]["timeout"], 120)

    def test_no_cross_origin_redirect(self):
        handler = upload.NoRedirect()
        req = upload.urllib.request.Request("https://stitch.googleapis.com", data=b"{}")
        self.assertIsNone(handler.redirect_request(req, None, 307, "redirect", {}, "https://example.invalid"))

    def test_payload_mappings(self):
        for mime, field in [("image/png", "screenshot"), ("text/html", "htmlCode")]:
            screen = upload.build_screen_request(mime, "eA==", title="/orders")["screen"]
            self.assertEqual(screen[field]["mimeType"], mime)
            self.assertEqual(screen["title"], "/orders")

    def test_markdown_is_not_accepted_by_private_rest_upload(self):
        self.assertNotIn(".md", upload._MIME_TYPES)

    def test_malformed_response_is_unknown_and_never_logged(self):
        malformed = [
            {}, [], None,
            {"results": [{"screen": {"name": "projects/123/screens/PRIVATE_CONTENT"}}]},
            {"screens": [{"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}], "screenInstances": [{"id": "PRIVATE_CONTENT", "sourceScreen": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]},
            {"results": []},
            {"results": {}},
            {"results": ["PRIVATE_CONTENT"]},
            {"results": [{"screen": {"name": {"secret": "PRIVATE_CONTENT"}}}]},
            {"results": [{"screen": {"name": "PRIVATE_CONTENT"}}]},
            {"results": [{"screen": {"name": "projects/999/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}]},
            {"results": [{"screen": {"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa?key=PRIVATE_CONTENT"}}]},
            {"screens": [{"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}], "screenInstances": {}},
            {"screens": [{"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}], "screenInstances": [None]},
            {"screens": [{"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}], "screenInstances": [{"id": {}, "sourceScreen": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]},
            {"screens": [{"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}], "screenInstances": [{"id": "contains PRIVATE_CONTENT", "sourceScreen": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]},
            {"screens": [{"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}], "screenInstances": [{"id": "11111111111111111111111111111111", "sourceScreen": []}]},
            {"screens": [{"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}], "screenInstances": [{"id": "11111111111111111111111111111111", "sourceScreen": "projects/123/screens/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]},
        ]
        for body in malformed:
            with self.subTest(body_type=type(body).__name__):
                output = io.StringIO()
                calls = []
                def transport(req, **kwargs):
                    calls.append(req)
                    return Response(json.dumps(body).encode())
                with contextlib.redirect_stdout(output), self.assertRaisesRegex(ValueError, "结果未知.*对账") as raised:
                    upload.call_batch_create_screens("https://stitch.googleapis.com", "offline-test-key", "123", [], urlopen=transport)
                self.assertEqual(len(calls), 1)
                self.assertNotIn("PRIVATE_CONTENT", output.getvalue() + str(raised.exception))

    def test_valid_response_returns_only_validated_identifiers(self):
        body = {
            "results": [{"screen": {"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "htmlCode": {"private": "PRIVATE_CONTENT"}}}],
            "private": "PRIVATE_CONTENT",
        }
        result = upload.call_batch_create_screens(
            "https://stitch.googleapis.com", "offline-test-key", "123", [],
            urlopen=lambda *args, **kwargs: Response(json.dumps(body).encode()),
        )
        self.assertEqual(result, {"screens": [{"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]})

    def test_cli_unknown_response_exits_without_private_output_or_retry(self):
        for body in [{}, [], {"screens": [{"name": {"secret": "PRIVATE_CONTENT"}}]}]:
            with self.subTest(body_type=type(body).__name__), tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / "orders.html"
                source.write_text("<h1>预约列表</h1>")
                output, errors = io.StringIO(), io.StringIO()
                with patch.dict(os.environ, {"STITCH_API_KEY": "offline-test-key"}), \
                     patch("sys.argv", ["upload", "--project-id", "123", "--file-path", str(source)]), \
                     patch("urllib.request.build_opener") as opener, \
                     contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    opener.return_value.open.return_value = Response(json.dumps(body).encode())
                    with self.assertRaises(SystemExit) as raised:
                        runpy.run_path(str(Path(__file__).parents[1] / "scripts/upload_to_stitch.py"), run_name="__main__")
                    self.assertEqual(raised.exception.code, 1)
                    self.assertEqual(opener.return_value.open.call_count, 1)
                self.assertIn("结果未知", errors.getvalue())
                self.assertIn("对账", errors.getvalue())
                self.assertNotIn("PRIVATE_CONTENT", output.getvalue() + errors.getvalue())
                self.assertNotIn("offline-test-key", output.getvalue() + errors.getvalue())

    def test_empty_or_non_json_body_is_unknown(self):
        for body in [b"", b"PRIVATE_CONTENT"]:
            with self.subTest(body_length=len(body)), self.assertRaisesRegex(ValueError, "结果未知.*对账") as raised:
                upload.call_batch_create_screens(
                    "https://stitch.googleapis.com", "offline-test-key", "123", [],
                    urlopen=lambda *args, **kwargs: Response(body),
                )
            self.assertNotIn("PRIVATE_CONTENT", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
