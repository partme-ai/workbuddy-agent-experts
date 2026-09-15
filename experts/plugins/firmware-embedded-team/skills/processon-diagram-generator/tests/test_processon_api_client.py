import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "processon_api_client.py"
SPEC = importlib.util.spec_from_file_location("processon_api_client", MODULE_PATH)
CLIENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIENT)

UPDATE_SPEC = importlib.util.spec_from_file_location(
    "processon_check_update", MODULE_PATH.parent / "check_update.py"
)
UPDATE = importlib.util.module_from_spec(UPDATE_SPEC)
UPDATE_SPEC.loader.exec_module(UPDATE)


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, payload=b"{}"):
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class ProcessOnClientTest(unittest.TestCase):
    def test_version_comparison(self):
        self.assertGreater(UPDATE.version_tuple("2.4.1"), UPDATE.version_tuple("2.4.0"))
        with self.assertRaises(ValueError):
            UPDATE.version_tuple("not-a-version")

    def test_bearer_header_is_normalized(self):
        headers = CLIENT.build_headers("secret")
        self.assertEqual("Bearer secret", headers["Authorization"])
        self.assertNotIn("secret", json.dumps(CLIENT.build_stream_payload("prompt")))

    def test_transient_errors_retry_with_bounded_backoff(self):
        attempts = []
        sleeps = []

        def opener(_request, timeout):
            attempts.append(timeout)
            if len(attempts) < 3:
                raise urllib.error.URLError("temporary")
            return FakeResponse()

        response = CLIENT.open_json_request(
            "https://example.invalid",
            {},
            {"prompt": "x"},
            timeout=7,
            opener=opener,
            sleeper=sleeps.append,
        )
        self.assertIsInstance(response, FakeResponse)
        self.assertEqual([7, 7, 7], attempts)
        self.assertEqual([1, 2], sleeps)

    def test_authentication_error_is_not_retried(self):
        attempts = []

        def opener(request, timeout):
            attempts.append(timeout)
            raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", {}, io.BytesIO())

        with self.assertRaises(urllib.error.HTTPError):
            CLIENT.open_json_request(
                "https://example.invalid",
                {},
                {},
                opener=opener,
                sleeper=lambda _delay: self.fail("must not sleep for 401"),
            )
        self.assertEqual(1, len(attempts))

    def test_rendered_image_uses_explicit_output_directory(self):
        png = b"fake-png"
        payload = {"content": [{"type": "image", "mimeType": "image/png", "data": CLIENT.base64.b64encode(png).decode()}]}
        with tempfile.TemporaryDirectory() as temp_dir:
            result = CLIENT.build_final_image_payload(payload, "test", output_dir=temp_dir)
            saved = Path(result["data"]["primarySavedImagePath"])
            self.assertEqual(Path(temp_dir), saved.parent)
            self.assertEqual(png, saved.read_bytes())


if __name__ == "__main__":
    unittest.main()
