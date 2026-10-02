"""Regression coverage for the real Explore script entry point."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class ExploreStartupTests(unittest.TestCase):
    def assert_help(self, cwd):
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/explore/main.py"), "--help"],
            cwd=str(cwd), env=env, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Deep discovery pipeline", result.stdout)
        self.assertNotIn("ModuleNotFoundError: No module named 'scripts'", result.stderr)

    def test_help_from_repository_without_pythonpath(self):
        self.assert_help(REPO_ROOT)

    def test_help_from_external_directory_without_pythonpath(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assert_help(directory)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
