"""Real subprocess adapter contracts, with isolated executable fixtures."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from scripts.explore import probe_chain as probe

ROOT = Path(__file__).resolve().parents[1]
NORMAL = '<html><title>Normal</title><article>Wiki content</article></html>'


class FallbackContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.output = self.root / 'page.html'

    def executable(self, name, source):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('#!' + sys.executable + '\n' + source)
        p.chmod(0o755)
        return str(p)

    def obscura(self, html=NORMAL, code=0):
        cli = self.executable('obscura',
            'import sys\n'
            'assert sys.argv[1:] == ["fetch", "https://example.invalid", "--dump", "html", "--quiet"], sys.argv\n'
            'print("diagnostic stderr", file=sys.stderr)\n'
            f'sys.stdout.write({html!r})\nsys.exit({code})\n')
        with patch.object(probe, '_obscura_preflight', return_value={'ok': True, 'path': cli}):
            return probe._run_obscura_fetch(str(ROOT), 'https://example.invalid', str(self.output))

    def test_obscura_supported_argv_and_stdout(self):
        result = self.obscura()
        self.assertEqual(result['status'], 'success', result)
        self.assertEqual(self.output.read_text(), NORMAL)

    def test_obscura_never_promotes_stale_output(self):
        for html, code, reason in [('', 0, 'missing_output'), (NORMAL, 2, 'unknown')]:
            with self.subTest(code=code):
                self.output.write_text(NORMAL)
                result = self.obscura(html, code)
                self.assertEqual(result['status'], 'failure')
                self.assertEqual(result['error_type'], reason)
                self.assertNotIn('output_path', result)

    def test_obscura_challenge_is_rejected_and_stderr_separate(self):
        html = (ROOT / 'tests/fixtures/challenge-wikigg.html').read_text()
        result = self.obscura(html)
        self.assertEqual(result['status'], 'failure')
        self.assertFalse(result['admission']['admitted'])
        self.assertEqual(self.output.read_text(), html)
        self.assertEqual(Path(str(self.output) + '.stderr.txt').read_text(), 'diagnostic stderr\n')

    def cloak_setup(self):
        import shutil
        scripts = self.root / 'scripts'
        scripts.mkdir()
        shutil.copy(ROOT / 'scripts/cloakbrowser-cli.sh', scripts)
        (self.root / 'configs').mkdir()
        shutil.copy(ROOT / 'configs/engine-versions.json', self.root / 'configs')
        (scripts / 'cloakbrowser_fetcher.py').write_text('# intercepted by fixture executable\n')
        managed = self.root / 'custom-root'
        python_source = ('import sys,json\n'
                         'if "-c" not in sys.argv:\n'
                         f'    print(json.dumps({{"success":True,"html":{NORMAL!r}}}))\n')
        return managed, python_source

    def test_cloak_custom_root_preflight(self):
        managed, source = self.cloak_setup()
        self.executable('custom-root/bin/python', source)
        with patch.dict(os.environ, {'CLOAKBROWSER_MANAGED_ROOT': str(managed)}):
            result = probe._run_cloakbrowser_fetch(str(self.root), 'https://example.invalid', str(self.output))
        self.assertEqual(result['status'], 'success', result)
        self.assertEqual(self.output.read_text(), NORMAL)

    def test_cloak_missing_environment_is_lazily_installed(self):
        managed, source = self.cloak_setup()
        # Run the real shell preflight; only replace uv's external installation boundary.
        self.executable('bin/uv', 'import os,sys,pathlib\n'
                        'if sys.argv[1] == "pip": assert sys.argv[-1] == "cloakbrowser==0.4.3", sys.argv\n'
                        f'p=pathlib.Path({str(managed / "bin/python")!r})\n'
                        'p.parent.mkdir(parents=True,exist_ok=True)\n'
                        f'p.write_text({("#!" + sys.executable + chr(10) + source)!r})\n'
                        'p.chmod(0o755)\n')
        with patch.dict(os.environ, {'CLOAKBROWSER_MANAGED_ROOT': str(managed),
                                    'PATH': str(self.root / 'bin') + os.pathsep + os.environ['PATH']}):
            result = probe._run_cloakbrowser_fetch(str(self.root), 'https://example.invalid', str(self.output))
        self.assertEqual(result['status'], 'success', result)
        self.assertTrue((managed / 'bin/python').exists())

    def test_cloak_invalid_preflight_never_runs_fetch(self):
        scripts = self.root / 'scripts'
        scripts.mkdir()
        (scripts / 'cloakbrowser_fetcher.py').write_text('raise AssertionError("must not execute")')
        for body in ['exit 2', 'echo STATUS=available', 'echo STATUS=missing\necho RESOLVED_CLI_PATH=/bin/sh',
                     'echo STATUS=available\necho RESOLVED_CLI_PATH=/nonexistent']:
            (scripts / 'cloakbrowser-cli.sh').write_text(body)
            result = probe._run_cloakbrowser_fetch(str(self.root), 'https://example.invalid', str(self.output))
            self.assertEqual(result['error_type'], 'preflight_failed', result)
            self.assertFalse(self.output.exists())

    def test_probe_persists_mixed_failure_stages_and_pending(self):
        failures = [probe._build_success('scrapling-get', (ROOT / 'tests/fixtures/challenge-wikigg.html').read_text(), str(self.output)),
                    probe._build_failure('obscura-fetch', "unexpected argument '--output'", process_exit=2),
                    {'engine':'cloakbrowser-fetch','status':'failure','error_type':'preflight_failed','detail':'missing'}]
        with patch.object(probe, '_run_scrapling_get', return_value=failures[0]), \
             patch.object(probe, '_run_obscura_fetch', return_value=failures[1]), \
             patch.object(probe, '_run_cloakbrowser_fetch', return_value=failures[2]):
            result = probe.probe(str(ROOT), 'https://example.invalid', str(self.root))
        self.assertIsNone(result['success_engine'])
        self.assertEqual([r['stage'] for r in result['results']], ['admission','process','preflight','pending'])
        self.assertEqual(result['results'][1]['error_type'], 'invalid_invocation')
        self.assertFalse(result['results'][-1]['executed'])
        self.assertTrue(Path(result['diagnostic_path']).is_file())
        self.assertEqual(json.loads(Path(result['diagnostic_path']).read_text())['results'], result['results'])

    def test_cloak_invalid_json_reports_protocol_failure(self):
        managed, _ = self.cloak_setup()
        self.executable('custom-root/bin/python', 'import sys\nif "-c" not in sys.argv: print("not JSON")\n')
        with patch.dict(os.environ, {'CLOAKBROWSER_MANAGED_ROOT': str(managed)}):
            result = probe._run_cloakbrowser_fetch(str(self.root), 'https://example.invalid', str(self.output))
        self.assertEqual(result['error_type'], 'invalid_response')
        self.assertFalse(self.output.exists())
