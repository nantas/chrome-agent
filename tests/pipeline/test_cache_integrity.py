"""Persistent cache identity and compatibility contracts."""
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from scripts.pipeline.pipeline import cache


class CacheIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.args = (self.root, 'mediawiki', 'example.test')

    def test_exact_titles_roundtrip_and_concurrent_writes(self):
        titles = ['A/B', 'A_B', 'A:B', 'A B', '花/🌱', 'Long' * 200]
        def save(title):
            return cache.save_page_cache(*self.args, {'title': title, 'html': '<p>' + title + '</p>'})
        with ThreadPoolExecutor(max_workers=4) as executor:
            paths = list(executor.map(save, titles * 3))
        self.assertEqual(len(set(paths)), len(titles))
        self.assertEqual(cache.list_cached_pages(*self.args), set(titles))
        for title in titles:
            self.assertEqual(cache.load_page_cache(*self.args, title)['html'], '<p>' + title + '</p>')
        self.assertFalse(list(paths[0].parent.glob('.tmp*')))

    def test_legacy_read_and_identity_validation(self):
        directory = cache.get_domain_cache_dir(*self.args)
        legacy = directory / 'A_B.json'
        original = json.dumps({'title': 'A/B', 'html': '<p>old</p>'})
        legacy.write_text(original)
        self.assertEqual(cache.load_page_cache(*self.args, 'A/B')['html'], '<p>old</p>')
        self.assertIsNone(cache.load_page_cache(*self.args, 'A_B'))
        self.assertEqual(legacy.read_text(), original)
        cache.save_page_cache(*self.args, {'title': 'A/B', 'html': '<p>new</p>'})
        self.assertEqual(cache.load_page_cache(*self.args, 'A/B')['html'], '<p>new</p>')
        (directory / 'Bad.json').write_text('{')
        self.assertIsNone(cache.load_page_cache(*self.args, 'Bad'))
        self.assertEqual(cache.list_cached_pages(*self.args), {'A/B'})

    def test_legacy_paths_stay_in_cache_directory(self):
        directory = cache.get_domain_cache_dir(*self.args)
        (directory.parent / 'Escape.json').write_text(json.dumps({'title': '../Escape', 'html': 'wrong'}))
        self.assertIsNone(cache.load_page_cache(*self.args, '../Escape'))
        (directory / 'No_Title.json').write_text(json.dumps({'html': 'unknown'}))
        self.assertIsNone(cache.load_page_cache(*self.args, 'No Title'))
