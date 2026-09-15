"""Test both fetch helpers with a local curl stand-in, never a network call."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class FetchTests(unittest.TestCase):
    def test_failure_preserves_output_and_success_replaces(self):
        skills = Path(__file__).resolve().parents[2]
        for name in ('stitch-react-native', 'stitch-react-components'):
            with self.subTest(skill=name), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                curl = root / 'curl'
                curl.write_text('#!/bin/bash\nwhile [ "$#" -gt 0 ]; do\n if [ "$1" = "-o" ]; then shift; dest="$1"; fi\n shift\ndone\nprintf "asset" > "$dest"\nexit "${FETCH_TEST_STATUS:-1}"\n')
                curl.chmod(0o700)
                output = root / 'existing.html'
                output.write_text('old')
                env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'])
                script = skills / name / 'scripts/fetch-stitch.sh'
                args = ['bash', str(script), 'https://example.invalid/asset?private=redacted', str(output)]
                result = subprocess.run(args, env=env, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(output.read_text(), 'old')
                self.assertNotIn('private=', result.stdout + result.stderr)
                self.assertEqual(list(root.glob('*.download.*')), [])
                result = subprocess.run(args, env=dict(env, FETCH_TEST_STATUS='0'), capture_output=True, text=True)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(output.read_text(), 'asset')


if __name__ == '__main__':
    unittest.main()
