"""Tests for scripts.pipeline.pipeline.phases.fetch_cdp_api."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Module under test — imported after we create it (GREEN phase)


class TestFetchCdpApi(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = self.tmpdir.name
        # Create .cache structure
        os.makedirs(Path(self.repo_root) / ".cache" / "chrome-cdp", exist_ok=True)

        self.strategy = {
            "domain": "maker.taptap.cn",
            "api": {
                "platform": "rest",
                "auth": {
                    "source": "localStorage",
                    "key": "taptap_access_token",
                    "header_format": "Bearer {token}",
                },
                "endpoints": {
                    "list": {"url": "/api/v1/docs/list", "method": "GET"},
                    "content": {"url": "/api/v1/docs/content", "method": "GET"},
                },
            },
        }
        self.domain = "maker.taptap.cn"
        self.project_id = "test-project-123"

        # Sample list API response
        self.list_response = json.dumps({
            "success": True,
            "data": [
                {"type": "resource_link", "name": "design/GDD-拼词肉鸽.md", "size": 53999,
                 "uri": "file:///workspace/docs/design/GDD-拼词肉鸽.md"},
                {"type": "resource_link", "name": "design/content/Boss内容设计.md", "size": 8224,
                 "uri": "file:///workspace/docs/design/content/Boss内容设计.md"},
                {"type": "resource_link", "name": "design/systems", "mimeType": "inode/directory",
                 "uri": "file:///workspace/docs/design/systems"},
                {"type": "resource_link", "name": "GDD.md", "size": 30964,
                 "uri": "file:///workspace/docs/GDD.md"},
            ],
        })

        # Sample content API response
        self.content_response = "# GDD：拼词肉鸽\n\n> 主设计文档\n\n## 系统设计"

    def tearDown(self):
        self.tmpdir.cleanup()

    # ------------------------------------------------------------------
    # Helper: build a mock eval_fn that returns predefined responses
    # ------------------------------------------------------------------

    def _make_eval_fn(self, responses_by_expr_prefix):
        """responses_by_expr_prefix: dict of {prefix: response_value}"""
        def eval_fn(js_expr: str):
            for prefix, value in responses_by_expr_prefix.items():
                if prefix in js_expr:
                    return value
            return None
        return eval_fn

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_successful_list_and_content_flow(self):
        """3.1 SPEC: Successful list and content retrieval"""
        from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api

        eval_fn = self._make_eval_fn({
            "taptap_access_token": '{"token":"fake-jwt"}',
            "/api/v1/docs/list": self.list_response,
            "/api/v1/docs/content": self.content_response,
        })

        results = run_fetch_cdp_api(
            eval_fn=eval_fn,
            strategy=self.strategy,
            domain=self.domain,
            repo_root=self.repo_root,
            project_id=self.project_id,
            batch_delay_sec=0,
        )

        # 3 files (directory entry filtered out), 1 skipped (GDD.md - no prefix match? Wait
        # actually all 3 files should match since path_prefix defaults to None = match all)
        self.assertGreaterEqual(len(results), 1)

        # Check structure of first result
        first_key = list(results.keys())[0]
        entry = results[first_key]
        self.assertIn("title", entry)
        self.assertIn("status", entry)
        self.assertIn("content", entry)

    def test_path_prefix_filtering(self):
        """Files not matching path_prefix are excluded."""
        from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api

        eval_fn = self._make_eval_fn({
            "taptap_access_token": '{"token":"fake-jwt"}',
            "/api/v1/docs/list": self.list_response,
            "/api/v1/docs/content": self.content_response,
        })

        results = run_fetch_cdp_api(
            eval_fn=eval_fn,
            strategy=self.strategy,
            domain=self.domain,
            repo_root=self.repo_root,
            project_id=self.project_id,
            path_prefix="design/content/",
            batch_delay_sec=0,
        )

        # Only design/content/Boss内容设计.md should match
        keys = list(results.keys())
        self.assertEqual(len(keys), 1)
        self.assertIn("Boss", keys[0])

    def test_directory_entries_filtered_out(self):
        """List entries with mimeType: inode/directory are excluded."""
        from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api

        eval_fn = self._make_eval_fn({
            "taptap_access_token": '{"token":"fake-jwt"}',
            "/api/v1/docs/list": self.list_response,
            "/api/v1/docs/content": self.content_response,
        })

        results = run_fetch_cdp_api(
            eval_fn=eval_fn,
            strategy=self.strategy,
            domain=self.domain,
            repo_root=self.repo_root,
            project_id=self.project_id,
            batch_delay_sec=0,
        )

        # 4 entries total, 1 directory → 3 files
        self.assertEqual(len(results), 3)

    def test_token_failure_returns_empty(self):
        """SPEC: Token extraction failure returns empty results."""
        from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api

        eval_fn = self._make_eval_fn({
            # token call returns None → failure
        })

        results = run_fetch_cdp_api(
            eval_fn=eval_fn,
            strategy=self.strategy,
            domain=self.domain,
            repo_root=self.repo_root,
            project_id=self.project_id,
            batch_delay_sec=0,
        )

        self.assertEqual(len(results), 0)

    def test_list_api_failure_returns_empty(self):
        """SPEC: List API failure returns empty results."""
        from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api

        eval_fn = self._make_eval_fn({
            "taptap_access_token": '{"token":"fake-jwt"}',
            # list API returns None → failure
        })

        results = run_fetch_cdp_api(
            eval_fn=eval_fn,
            strategy=self.strategy,
            domain=self.domain,
            repo_root=self.repo_root,
            project_id=self.project_id,
            batch_delay_sec=0,
        )

        self.assertEqual(len(results), 0)

    def test_single_content_failure_skips_file(self):
        """SPEC: Single content failure does not block the batch."""
        from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api

        call_count = {"content": 0}

        def eval_fn(js_expr: str):
            if "taptap_access_token" in js_expr:
                return '{"token":"fake-jwt"}'
            if "/api/v1/docs/list" in js_expr:
                return self.list_response
            if "/api/v1/docs/content" in js_expr:
                call_count["content"] += 1
                # Fail the first content call, succeed the rest
                if call_count["content"] == 1:
                    return None
                return self.content_response
            return None

        results = run_fetch_cdp_api(
            eval_fn=eval_fn,
            strategy=self.strategy,
            domain=self.domain,
            repo_root=self.repo_root,
            project_id=self.project_id,
            batch_delay_sec=0,
        )

        # 3 files total, 1 failed → 2 succeeded
        succeeded = sum(1 for r in results.values() if r["status"] == "ok")
        self.assertEqual(succeeded, 2)
        failed = sum(1 for r in results.values() if r["status"] == "error")
        self.assertEqual(failed, 1)

    def test_cache_hit_skips_fetch(self):
        """SPEC: Cached file is skipped unless re_fetch=True."""
        from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api
        from scripts.pipeline.pipeline import cache as cache_mod

        # Pre-populate cache for one file
        safe_path = "design_GDD-拼词肉鸽.md"
        cache_mod.save_page_cache(
            self.repo_root, "chrome-cdp", self.domain,
            {"title": safe_path, "name": "design/GDD-拼词肉鸽.md",
             "content": "cached content", "fetched_at": "2026-01-01T00:00:00"},
        )

        content_call_count = [0]

        def eval_fn(js_expr: str):
            if "taptap_access_token" in js_expr:
                return '{"token":"fake-jwt"}'
            if "/api/v1/docs/list" in js_expr:
                return self.list_response
            if "/api/v1/docs/content" in js_expr:
                content_call_count[0] += 1
                return self.content_response
            return None

        results = run_fetch_cdp_api(
            eval_fn=eval_fn,
            strategy=self.strategy,
            domain=self.domain,
            repo_root=self.repo_root,
            project_id=self.project_id,
            batch_delay_sec=0,
        )

        # 3 files total, 1 cached → only 2 content API calls
        self.assertEqual(content_call_count[0], 2)
        # Check cached entry was used
        gdd_result = results.get(safe_path)
        self.assertIsNotNone(gdd_result)
        self.assertEqual(gdd_result["content"], "cached content")

    def test_re_fetch_bypasses_cache(self):
        """SPEC: re_fetch=True forces re-fetch for all files."""
        from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api
        from scripts.pipeline.pipeline import cache as cache_mod

        safe_path = "design_GDD-拼词肉鸽.md"
        cache_mod.save_page_cache(
            self.repo_root, "chrome-cdp", self.domain,
            {"title": safe_path, "name": "design/GDD-拼词肉鸽.md",
             "content": "cached content", "fetched_at": "2026-01-01T00:00:00"},
        )

        content_call_count = [0]

        def eval_fn(js_expr: str):
            if "taptap_access_token" in js_expr:
                return '{"token":"fake-jwt"}'
            if "/api/v1/docs/list" in js_expr:
                return self.list_response
            if "/api/v1/docs/content" in js_expr:
                content_call_count[0] += 1
                return self.content_response
            return None

        results = run_fetch_cdp_api(
            eval_fn=eval_fn,
            strategy=self.strategy,
            domain=self.domain,
            repo_root=self.repo_root,
            project_id=self.project_id,
            re_fetch=True,
            batch_delay_sec=0,
        )

        # All 3 files fetched
        self.assertEqual(content_call_count[0], 3)
        # Cached entry was overwritten
        gdd_result = results.get(safe_path)
        self.assertEqual(gdd_result["content"], self.content_response)


if __name__ == "__main__":
    unittest.main()
