"""Tests for scripts.explore.probe_chain builder helpers.

Validates _build_success / _build_failure construct the expected dict shape
extracted from the three engine runners. Pure-function tests (no subprocess).
"""

import unittest

from scripts.explore.probe_chain import _build_success, _build_failure


class TestBuildSuccess(unittest.TestCase):
    def test_full_success_dict(self):
        html = "<html><head><title>My Page</title></head><body>x</body></html>"
        r = _build_success("scrapling-get", html, "/tmp/out.html")
        self.assertEqual(r["engine"], "scrapling-get")
        self.assertEqual(r["status"], "success")
        self.assertEqual(r["http_status"], 200)
        self.assertEqual(r["page_title"], "My Page")
        self.assertEqual(r["content_length"], len(html))
        self.assertEqual(r["output_path"], "/tmp/out.html")

    def test_empty_html_zero_length_null_title(self):
        r = _build_success("obscura-fetch", None, "/p")
        self.assertEqual(r["content_length"], 0)
        self.assertIsNone(r["page_title"])


class TestBuildFailure(unittest.TestCase):
    def test_failure_with_http_status(self):
        r = _build_failure("scrapling-get", "HTTP 403 forbidden", 403)
        self.assertEqual(r["engine"], "scrapling-get")
        self.assertEqual(r["status"], "failure")
        self.assertEqual(r["http_status"], 403)
        self.assertEqual(r["error_type"], "cloudflare-managed")
        self.assertEqual(r["detail"], "HTTP 403 forbidden")

    def test_detail_truncated_to_500(self):
        long_stderr = "x" * 1000
        r = _build_failure("obscura-fetch", long_stderr)
        self.assertEqual(len(r["detail"]), 500)

    def test_stdout_fallback_when_stderr_empty(self):
        # cloakbrowser runner passes result.stdout; detail should fall back to it
        r = _build_failure("cloakbrowser-fetch", "", None, "fallback stdout")
        self.assertEqual(r["detail"], "fallback stdout")

    def test_stderr_preferred_over_stdout(self):
        r = _build_failure("cloakbrowser-fetch", "real stderr", None, "stdout")
        self.assertEqual(r["detail"], "real stderr")

    def test_unknown_error_type(self):
        r = _build_failure("x", "something weird happened", None)
        self.assertEqual(r["error_type"], "unknown")


if __name__ == "__main__":
    unittest.main()
