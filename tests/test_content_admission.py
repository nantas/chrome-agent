"""Content admission regressions using sanitized interstitial evidence."""
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch
from scripts.explore import probe_chain

FIXTURE = Path(__file__).parent / 'fixtures' / 'challenge-wikigg.html'

class AdmissionTests(unittest.TestCase):
    def test_probe_rejects_zero_exit_challenge(self):
        def engine(command, **kwargs):
            Path(command[4]).write_text(FIXTURE.read_text())
            return CompletedProcess(command, 0, '', '')
        with tempfile.TemporaryDirectory() as tmp, patch.object(probe_chain, '_scrapling_preflight', return_value={'ok': True, 'resolvedCliPath': 'offline'}), patch.object(probe_chain.subprocess, 'run', side_effect=engine):
            result = probe_chain._run_scrapling_get('.', 'https://example.invalid', str(Path(tmp)/'out.html'))
        self.assertEqual(result['status'], 'failure')
        self.assertIsNone(result['http_status'])
        self.assertEqual(result['admission']['reason'], 'challenge_page')

    def test_normal_content_and_output_errors(self):
        from scripts.lib.content_admission import classify_html, admit_html_file
        from scripts.explore.protection_identifier import identify
        normal = '<title>Cloudflare guide</title><article><h1>Just a moment</h1><p>Documentation</p><code>&lt;script src="/challenge-platform/x"&gt;</code></article><iframe src="https://challenges.cloudflare.com/turnstile"></iframe>'
        self.assertTrue(classify_html(normal)['admitted'])
        self.assertEqual(identify([], normal)['type'], 'none')
        self.assertFalse(classify_html(normal, 403)['admitted'])
        self.assertIsNone(classify_html(normal, 403)['protection_type'])
        for status in (200, None):
            self.assertFalse(classify_html(FIXTURE.read_text(), status)['admitted'])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(admit_html_file(tmp)['reason'], 'unreadable_output')
            self.assertEqual(admit_html_file(tmp+'/missing')['reason'], 'missing_output')
            p = Path(tmp)/'empty'; p.write_text(' ')
            self.assertEqual(admit_html_file(p)['reason'], 'empty_content')

    def test_probe_defends_success_candidates_and_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp)/'bad.html'; bad.write_text(FIXTURE.read_text())
            good = Path(tmp)/'good.html'; good.write_text('<h1>Article</h1><p>Body</p>')
            with patch.object(probe_chain, '_run_scrapling_get', return_value={'status':'success','engine':'scrapling-get','output_path':str(bad)}), patch.object(probe_chain, '_run_obscura_fetch', return_value={'status':'success','engine':'obscura-fetch','output_path':str(good)}) as later:
                result = probe_chain.probe('.', 'https://example.invalid', tmp)
            self.assertEqual(result['success_engine'], 'obscura-fetch')
            self.assertEqual(later.call_count, 1)
            self.assertEqual(result['results'][0]['status'], 'failure')
            self.assertEqual(result['html_content'], good.read_text())

    def test_main_stops_without_admitted_content(self):
        import io
        import json
        from contextlib import redirect_stdout
        from scripts.explore import main as workflow
        with tempfile.TemporaryDirectory() as tmp, patch('sys.argv', ['main', tmp, 'https://example.invalid', '--run-dir', tmp]), patch.object(workflow, 'probe', return_value={'results':[], 'success_engine':None, 'html_content':None}), patch.object(workflow, 'generate') as generate, patch.object(workflow, 'map_structure') as mapping, patch.object(workflow, 'discover') as discover, patch.object(workflow, 'convert') as convert:
            stream = io.StringIO()
            with redirect_stdout(stream), self.assertRaises(SystemExit) as exit_result:
                workflow.main()
            self.assertEqual(exit_result.exception.code, 3)
            self.assertEqual(json.loads(stream.getvalue())['result'], 'failure')
            for fn in (generate, mapping, discover, convert):
                fn.assert_not_called()

    def test_rejected_sample_does_not_convert(self):
        from scripts.explore import sample_converter as samples
        def fetch(root, url, engine, output):
            Path(output).write_text(FIXTURE.read_text())
            return {'ok': True}
        with tempfile.TemporaryDirectory() as tmp, patch.object(samples, '_fetch_sample', side_effect=fetch), patch.object(samples, '_apply_extraction') as convert:
            result = samples.convert('.', [{'title':'Bad','url':'https://example.invalid'}], {}, 'get', tmp)
        self.assertFalse(result[0]['ok'])
        convert.assert_not_called()

    def test_cache_admission_rejects_challenge(self):
        from scripts.pipeline.pipeline.cache import admit_page
        raw = {'title':'Bad', 'html':FIXTURE.read_text(), 'content_acquisition':'html_rendered'}
        admitted, error = admit_page(raw, 'Bad', 'html_rendered')
        self.assertIsNone(admitted)
        self.assertEqual(error['reason'], 'challenge_page')

    def test_cdp_does_not_cache_or_convert_challenge(self):
        from scripts.pipeline.pipeline.phases.fetch_cdp import run_fetch_cdp
        from scripts.pipeline.pipeline.phases.convert_html import run_convert_html
        from scripts.pipeline.pipeline import cache
        page = {'url':'https://example.invalid/Bad', 'title':'Bad'}
        with tempfile.TemporaryDirectory() as tmp:
            result = run_fetch_cdp([page], 'example.invalid', tmp, lambda url: {'html':FIXTURE.read_text()}, batch_delay_sec=0)
            self.assertEqual(result['failed'],1)
            cache.save_page_cache(tmp, 'chrome-cdp', 'example.invalid', {'title':'Bad','html':FIXTURE.read_text()})
            result = run_convert_html([page], 'example.invalid', tmp, tmp+'/out')
            self.assertEqual(result['failed'],1)
            self.assertFalse((Path(tmp)/'out/Bad.md').exists())

    def test_cloak_adapter_decodes_real_envelope(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp)/'page.html')
            envelope = {'success':True, 'html':FIXTURE.read_text(), 'http_status':200}
            with patch.object(probe_chain, '_cloakbrowser_preflight', return_value={'ok': True, 'path': 'fixture-python'}), patch.object(probe_chain.subprocess, 'run', return_value=CompletedProcess([],0,json.dumps(envelope),'')):
                result = probe_chain._run_cloakbrowser_fetch(str(Path.cwd()), 'https://example.invalid', output)
            self.assertEqual(result['status'], 'failure')
            self.assertEqual(result['admission']['reason'], 'challenge_page')

    def test_cloak_normal_title_is_not_rejected(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from scripts.cloakbrowser_fetcher import fetch_page
        page = MagicMock()
        page.title.return_value = 'Cloudflare attention guide'
        page.content.return_value = '<article>Normal documentation</article>'
        page.evaluate.return_value = 'Normal documentation'
        page.url = 'https://example.invalid'
        page.goto.return_value.status = 200
        browser = MagicMock()
        browser.new_context.return_value.new_page.return_value = page
        with patch.dict(sys.modules, {'cloakbrowser': SimpleNamespace(launch=lambda **kw: browser)}):
            result = fetch_page(page.url, timeout=0)
        self.assertTrue(result['success'], result.get('error'))
        self.assertEqual(result['http_status'], 200)
        self.assertEqual(result['html'], page.content.return_value)

    def test_normal_cross_path_equivalence(self):
        from scripts.lib.content_admission import classify_html
        from scripts.pipeline.pipeline.cache import admit_page
        from scripts.explore import sample_converter as samples
        html = '<article><h1>Normal</h1><p>Body</p></article>'
        self.assertTrue(classify_html(html)['admitted'])
        self.assertEqual(probe_chain._build_success('test', html, 'unused')['status'],'success')
        self.assertIsNone(admit_page({'title':'Normal','html':html},'Normal','html_rendered')[1])
        def fetch(root, url, engine, output):
            Path(output).write_text(html)
            return {'ok':True}
        with tempfile.TemporaryDirectory() as tmp, patch.object(samples,'_fetch_sample',side_effect=fetch):
            result = samples.convert('.', [{'title':'Normal','url':'https://example.invalid'}],{},'get',tmp)
        self.assertTrue(result[0]['ok'])
        self.assertIn('Body',result[0]['markdown'])

    def test_all_engines_blocked_remain_failure(self):
        bad = probe_chain._build_success('test', FIXTURE.read_text(), str(FIXTURE))
        with tempfile.TemporaryDirectory() as tmp, patch.object(probe_chain,'_run_scrapling_get',return_value=bad), patch.object(probe_chain,'_run_obscura_fetch',return_value=bad), patch.object(probe_chain,'_run_cloakbrowser_fetch',return_value=bad):
            result = probe_chain.probe('.', 'https://example.invalid', tmp)
        self.assertIsNone(result['success_engine'])
        self.assertIsNone(result['html_content'])
        self.assertEqual(len(result['results']),4)
        self.assertEqual(result['results'][-1]['status'],'pending')

    def test_zero_exit_without_new_output_does_not_reuse_old_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'old.html'; output.write_text('<p>Old body</p>')
            with patch.object(probe_chain,'_scrapling_preflight',return_value={'ok':True,'resolvedCliPath':'offline'}), patch.object(probe_chain.subprocess,'run',return_value=CompletedProcess([],0,'','')):
                result = probe_chain._run_scrapling_get('.', 'https://example.invalid', str(output))
            self.assertEqual(result['status'],'failure')
            self.assertEqual(output.read_text(),'<p>Old body</p>')
            self.assertEqual(result['process_exit'], 0)
            self.assertEqual(result['error_type'], 'missing_output')
