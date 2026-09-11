"""Fetch must admit cache payloads before skipping network acquisition."""
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from scripts.pipeline.pipeline import cache
from scripts.pipeline.pipeline.phases.fetch import run_fetch
from scripts.pipeline.strategies.acquisition import HtmlRenderedAcquisitionStrategy


class FakeClient:
    base_url = 'https://example.test/api.php'

    def __init__(self, html='<p>new</p>'):
        self.calls = []
        self.html = html

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        prop = kwargs['prop']
        return {'parse': {prop: {'*': self.html} if prop == 'text' else []}}


class AcquisitionCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.args = (self.root, 'mediawiki', 'example.test')
        self.strategy = {'api': {'platform': 'mediawiki', 'base_url': FakeClient.base_url,
                                 'content_profile': {'content_acquisition': 'html_rendered'}}}
        self.manifest = {'pages': [{'title': 'Old'}, {'title': 'Good'}]}
        self.rate = SimpleNamespace(concurrency=1, batch_delay_ms=0)

    def fetch(self, client, re_fetch=False):
        return run_fetch(client, self.manifest, self.strategy, self.rate, 'example.test',
                         HtmlRenderedAcquisitionStrategy(), self.root, re_fetch)

    def test_only_compatible_entries_skip(self):
        cache.save_page_cache(*self.args, {'title': 'Old', 'wikitext': 'old', 'content_acquisition': 'hybrid_wikitext_plus_rendered'})
        cache.save_page_cache(*self.args, {'title': 'Good', 'html': '<p>good</p>', 'content_acquisition': 'html_rendered'})
        client = FakeClient()
        stats = self.fetch(client)
        self.assertEqual((stats['fetched'], stats['skipped']), (1, 1))
        self.assertEqual({call['page'] for call in client.calls}, {'Old'})
        with patch('scripts.pipeline.pipeline.phases.fetch.ThreadPoolExecutor', side_effect=AssertionError('no executor')):
            self.assertEqual(self.fetch(FakeClient())['skipped'], 2)

    def test_re_fetch_and_invalid_fresh_html(self):
        for page in self.manifest['pages']:
            cache.save_page_cache(*self.args, {**page, 'html': '<p>cached</p>', 'content_acquisition': 'html_rendered'})
        self.assertEqual(self.fetch(FakeClient(), re_fetch=True)['fetched'], 2)
        stats = self.fetch(FakeClient(html=''), re_fetch=True)
        self.assertEqual(stats['failed'], 2)
        self.assertEqual(stats['failed_titles'], ['Good', 'Old'])
        self.assertEqual(stats['fetched'], 0)

    def test_admission_defaults_source_and_payload(self):
        self.assertEqual(cache.resolve_acquisition({}), 'wikitext_only')
        for raw, mode, reason in [
            ({'html': '<p>html</p>'}, 'html_rendered', None),
            ({'wikitext': ''}, 'wikitext_only', None),
            ({'html': '<p>html</p>', 'wikitext': 'wt'}, 'html_rendered', 'acquisition_mismatch'),
            ({'html': '<p>html</p>', 'content_acquisition': 'unknown'}, 'html_rendered', 'acquisition_mismatch'),
            ({'html': ' ', 'content_acquisition': 'html_rendered'}, 'html_rendered', 'missing_payload'),
            ({'wikitext': '{{#invoke:x}}', 'content_acquisition': 'hybrid_wikitext_plus_rendered'}, 'hybrid_wikitext_plus_rendered', 'missing_payload'),
            ({'wikitext': '{{Crop}}', 'content_acquisition': 'hybrid_wikitext_plus_rendered'}, 'hybrid_wikitext_plus_rendered', None),
            ({'html': '<p>html</p>', 'base_url': 'https://other/api.php'}, 'html_rendered', 'source_mismatch'),
        ]:
            with self.subTest(raw=raw, mode=mode):
                original = {'title': 'Page', **raw}
                admitted, error = cache.admit_page(original, 'Page', mode, FakeClient.base_url)
                self.assertEqual(error and error['reason'], reason)
                if not reason:
                    self.assertEqual(admitted['content_acquisition'], mode)
                self.assertEqual(original, {'title': 'Page', **raw})
