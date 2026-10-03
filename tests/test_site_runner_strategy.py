import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import test_runner


class SiteRunnerStrategyTests(unittest.TestCase):
    def test_mediawiki_cache_and_strategy_cleanup_are_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);domain='example.org';folder=root/'sites/strategies'/domain;folder.mkdir(parents=True)
            (folder/'strategy.md').write_text('---\ndomain: example.org\napi: {platform: mediawiki}\nextraction:\n  cleanup: [strip_footer]\n---\n')
            cache=root/'.cache/mediawiki'/domain;cache.mkdir(parents=True)
            (cache/'Example.json').write_text(json.dumps({'html':'<p>Body</p><div id="footer">FOOTER</div>'}))
            samples=folder/'samples';samples.mkdir();(samples/'Example.md').write_text('Body')
            with patch.object(test_runner,'REPO_ROOT',root):
                self.assertEqual(test_runner._resolve_cache_path('Example',domain),cache/'Example.json')
                case=test_runner._make_site_sample_test(domain,'Example','Example')('test_sample')
                result=unittest.TestResult();case.run(result)
                self.assertEqual(result.skipped,[]);self.assertTrue(result.wasSuccessful(),str(result.failures)+str(result.errors))
                import gzip
                (cache/'Example.json').unlink()
                portable=samples/'Example.html.gz'
                portable.write_bytes(gzip.compress(b'<p>Body</p><div id="footer">FOOTER</div>',mtime=0))
                self.assertEqual(test_runner._resolve_cache_path('Example',domain),portable)
                result=unittest.TestResult();case.run(result)
                self.assertTrue(result.wasSuccessful(),str(result.failures)+str(result.errors))

    def test_v2_cache_sample_is_found(self):
        from scripts.pipeline.pipeline.cache import save_page_cache
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            saved = save_page_cache(tmp, 'mediawiki', 'example.org', {'title': 'A/B', 'html': '<p>Body</p>'})
            with patch.object(test_runner, 'REPO_ROOT', root):
                self.assertEqual(test_runner._resolve_cache_path('A/B', 'example.org'), saved)

    def test_html_strategy_extraction_is_used_without_api(self):
        import gzip
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);domain='example.org';folder=root/'sites/strategies'/domain;folder.mkdir(parents=True)
            (folder/'strategy.md').write_text('---\ndomain: example.org\nextraction:\n  cleanup: [strip_footer]\n---\n')
            samples=folder/'samples';samples.mkdir();(samples/'Example.md').write_text('Body')
            (samples/'Example.html.gz').write_bytes(gzip.compress(b'<p>Body</p><div id="footer">FOOTER</div>',mtime=0))
            with patch.object(test_runner,'REPO_ROOT',root):
                case=test_runner._make_site_sample_test(domain,'Example','Example')('test_sample')
                result=unittest.TestResult();case.run(result)
                self.assertTrue(result.wasSuccessful(),str(result.failures)+str(result.errors))
