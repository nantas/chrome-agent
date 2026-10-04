"""Production conversion admission and resume evidence."""
import tempfile
import unittest
from pathlib import Path
from scripts.pipeline.pipeline import cache
from scripts.pipeline.pipeline.phases.convert import run_convert
from scripts.pipeline.pipeline.state import load_state, save_state


class ConversionResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.output = str(Path(self.root) / 'output')
        self.args = (self.root, 'mediawiki', 'example.test')
        self.page = {'title': 'Apple', 'target_directory': 'Crops', 'target_filename': 'Apple.md'}
        self.manifest = {'pages': [self.page]}
        self.strategy = {'api': {'platform': 'mediawiki', 'content_profile': {'content_acquisition': 'html_rendered'}}}
        self.file = Path(self.output) / 'Crops/Apple.md'
        self.file.parent.mkdir(parents=True)

    def run_conversion(self, resume=True):
        return run_convert(self.output, self.manifest, self.strategy, 'example.test', self.root, resume)

    def test_incompatible_cache_cannot_resume_old_output(self):
        cache.save_page_cache(*self.args, {'title': 'Apple', 'wikitext': 'old', 'content_acquisition': 'hybrid_wikitext_plus_rendered'})
        self.file.write_text('old markdown')
        save_state(self.output, {'completed_pages': ['Apple']})
        results, stats = self.run_conversion()
        self.assertEqual(results['Apple']['error'], 'cache_incompatible')
        self.assertEqual(stats['failed'], 1)
        self.assertNotIn('Apple', load_state(self.output)['completed_pages'])
        self.assertEqual(self.file.read_text(), 'old markdown')

    def test_challenge_cannot_resume_or_enter_assembly(self):
        from scripts.pipeline.pipeline.phases.assemble import run_assemble
        from scripts.pipeline.pipeline.registry import build_pipeline
        html = (Path(__file__).parents[1] / 'fixtures/challenge-wikigg.html').read_text()
        cache.save_page_cache(*self.args, {'title':'Apple','html':html,'content_acquisition':'html_rendered'})
        self.file.write_text('old markdown')
        save_state(self.output, {'completed_pages':['Apple']})
        results, stats = self.run_conversion()
        self.assertEqual(results['Apple']['reason'], 'challenge_page')
        self.assertEqual(stats['failed'], 1)
        self.assertNotIn('Apple', load_state(self.output)['completed_pages'])
        strategies = build_pipeline(self.strategy, 'example.test')
        run_assemble(self.output, self.manifest, results, self.strategy, 'example.test',
                     strategies.list_page_assembler, strategies.link_resolver)
        for index in Path(self.output).rglob('index.md'):
            self.assertNotIn('Apple.md', index.read_text())

    def test_resume_requires_current_fingerprint(self):
        raw = {'title': 'Apple', 'html': '<p>new</p>', 'content_acquisition': 'html_rendered'}
        cache.save_page_cache(*self.args, raw)
        self.file.write_text('old markdown')
        save_state(self.output, {'completed_pages': ['Apple']})
        results, stats = self.run_conversion()
        self.assertNotIn('skipped', results['Apple'])
        self.assertIn('new', self.file.read_text())
        results, stats = self.run_conversion()
        self.assertTrue(results['Apple']['skipped'])
        cache.save_page_cache(*self.args, {**raw, 'html': '<p>changed</p>'})
        results, stats = self.run_conversion()
        self.assertNotIn('skipped', results['Apple'])
        self.assertIn('changed', self.file.read_text())

    def test_pre_icon_semantics_cache_is_invalidated(self):
        from unittest.mock import patch
        raw = {'title': 'Apple', 'html': '<table><tr><th>A</th><th>B</th></tr><tr><td colspan="2"><img src="/a.png" alt="Blind"></td></tr></table>', 'content_acquisition': 'html_rendered'}
        cache.save_page_cache(*self.args, raw)
        with patch('scripts.pipeline.pipeline.phases.convert.CONVERTER_CONTRACT_REVISION', 7):
            self.run_conversion()
        self.assertNotIn('skipped', self.run_conversion()[0]['Apple'])
        self.assertIn('| Blind |', self.file.read_text())
        self.assertTrue(self.run_conversion()[0]['Apple']['skipped'])

    def test_context_changes_and_failed_write_invalidate_completion(self):
        from unittest.mock import patch
        raw = {'title': 'Apple', 'html': '<p>new</p>', 'content_acquisition': 'html_rendered'}
        cache.save_page_cache(*self.args, raw)
        self.run_conversion()
        cache.save_page_cache(*self.args, {**raw, 'fetched_at': 'later'})
        self.assertTrue(self.run_conversion()[0]['Apple']['skipped'])
        self.strategy['extraction'] = {'cleanup': ['strip_footer']}
        self.assertNotIn('skipped', self.run_conversion()[0]['Apple'])
        self.assertNotIn('skipped', self.run_conversion(resume=False)[0]['Apple'])
        with patch('scripts.pipeline.pipeline.phases.convert.CONVERTER_CONTRACT_REVISION', 999):
            self.assertNotIn('skipped', self.run_conversion()[0]['Apple'])
        self.page['target_directory'] = 'Misc'
        self.assertNotIn('skipped', self.run_conversion()[0]['Apple'])
        cache.save_page_cache(*self.args, {**raw, 'html': '<p>next</p>'})
        with patch('scripts.pipeline.pipeline.phases.convert.open', side_effect=OSError('write interrupted')):
            results, stats = self.run_conversion()
        self.assertEqual(stats['failed'], 1)
        self.assertNotIn('Apple', load_state(self.output)['completed_pages'])
        self.assertNotIn('Apple', load_state(self.output)['conversion_fingerprints'])

    def test_offline_fetch_convert_assemble_recovery(self):
        from types import SimpleNamespace
        from scripts.pipeline.pipeline.phases.fetch import run_fetch
        from scripts.pipeline.pipeline.phases.assemble import run_assemble
        from scripts.pipeline.pipeline.registry import build_pipeline
        from tests.pipeline.test_acquisition_cache import FakeClient
        broken = {'title': 'Broken', 'target_directory': 'Crops', 'target_filename': 'Broken.md'}
        self.manifest['pages'].append(broken)
        self.strategy['extraction'] = {'infobox': {'enabled': True, 'selector': '.portable-infobox'}}
        for page in self.manifest['pages']:
            cache.save_page_cache(*self.args, {'title': page['title'], 'wikitext': 'old', 'content_acquisition': 'hybrid_wikitext_plus_rendered'})
        self.file.write_text('old output')
        save_state(self.output, {'completed_pages': ['Apple', 'Broken']})
        html = '<aside class="portable-infobox"><div class="pi-data"><h3 class="pi-data-label">Seed Chance</h3><div class="pi-data-value">7.14%</div></div></aside><p>Body</p>'
        class Client(FakeClient):
            def parse(self, **kwargs):
                if kwargs['page'] == 'Broken':
                    raise RuntimeError('unavailable')
                return super().parse(**kwargs)
        strategies = build_pipeline(self.strategy, 'example.test')
        stats = run_fetch(Client(html), self.manifest, self.strategy,
                          SimpleNamespace(concurrency=1, batch_delay_ms=0), 'example.test',
                          strategies.content_acquisition, self.root)
        self.assertEqual((stats['fetched'], stats['failed']), (1, 1))
        results, stats = self.run_conversion()
        self.assertEqual(results['Broken']['status'], 'error')
        run_assemble(self.output, self.manifest, results, self.strategy, 'example.test',
                     strategies.list_page_assembler, strategies.link_resolver)
        self.assertIn('Seed Chance', self.file.read_text())
        self.assertIn('7.14%', self.file.read_text())
        self.assertFalse((self.file.parent / 'Broken.md').exists())
        self.assertNotIn('Broken', (self.file.parent / 'index.md').read_text())
        self.assertTrue(self.run_conversion()[0]['Apple']['skipped'])

    def test_orchestrator_retains_fingerprints_and_reports_failed_refetch(self):
        import argparse
        import json
        from unittest.mock import patch
        from scripts.pipeline.cli import _add_pipeline_args
        from scripts.pipeline.pipeline.orchestrator import run_pipeline
        raw = {'title': 'Apple', 'html': '<p>cached</p>', 'content_acquisition': 'html_rendered'}
        cache.save_page_cache(*self.args, raw)
        self.strategy['api']['base_url'] = 'https://example.test/api.php'
        manifest_path = Path(self.root) / 'manifest.json'
        self.page['ns'] = 0
        manifest_path.write_text(json.dumps(self.manifest))
        parser = argparse.ArgumentParser()
        _add_pipeline_args(parser)
        args = parser.parse_args(['https://example.test', '--strategy', 'unused.md',
                                  '--output', self.output, '--from-manifest', str(manifest_path),
                                  '--no-api-probe', '--no-auto-fix-links', '--phase', 'convert'])
        args.repo_root = self.root
        module = 'scripts.pipeline.pipeline.orchestrator.'
        with patch(module + 'parse_strategy', return_value=self.strategy), patch(module + 'validate_api_config', return_value=None):
            self.assertEqual(run_pipeline(args), 0)
            self.assertIn('Apple', load_state(self.output).get('conversion_fingerprints', {}))
            args.phase = ['all']
            args.re_fetch = True
            failed = {'total': 1, 'fetched': 0, 'skipped': 0, 'failed': 1, 'failed_titles': ['Apple']}
            with patch(module + 'run_fetch', return_value=failed):
                self.assertEqual(run_pipeline(args), 12)
                saved = json.loads((Path(self.output) / 'extraction_results.json').read_text())
                self.assertEqual(saved['pages']['Apple']['reason'], 'fetch_failed')
                self.assertNotIn('Apple', load_state(self.output)['completed_pages'])
                args.phase = ['fetch']
                self.assertEqual(run_pipeline(args), 12)
