"""Real conversion and quality checking through both Explore orchestrators."""
import contextlib
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/explore'))
main = importlib.import_module('main')
iterate = importlib.import_module('iterate')
converter = importlib.import_module('sample_converter')


class SourceIntegrationTests(unittest.TestCase):
    def test_main_and_iterate_share_real_source_checks(self):
        html = '<img src="https://example.org/skin.png"><main><p>of of</p><img src="https://example.org/body.png"></main>'
        rules = {'selectors': {'content': 'main'}}
        samples = [{'title': 'Test', 'url': 'https://example.org/wiki/Test'}]
        with tempfile.TemporaryDirectory() as directory:
            scaffold = Path(directory) / 'strategy.md'
            content = '---\n' + yaml.safe_dump({'domain': 'example.org', 'extraction': rules}) + '---\n'
            scaffold.write_text(content)
            def fetch(_root, _url, _engine, filename):
                Path(filename).write_text(html)
                return {'ok': True}
            with patch.object(converter, '_fetch_sample', side_effect=fetch):
                result = iterate.iterate(directory, str(scaffold), '', samples, 'offline', directory)
                self.assertTrue(result['self_check']['overall_pass'], result['self_check'])
                self.assertTrue(result['self_check']['notes'])
                capture = io.StringIO()
                with patch('sys.argv', ['main.py', directory, 'https://example.org', '--run-dir', directory, '--samples', json.dumps(samples)]), patch.object(main, 'probe', return_value={'success_engine':'offline','results':[],'html_content':''}), patch.object(main, 'discover', return_value=[]), patch.object(main, 'identify', return_value={}), patch.object(main, 'generate', return_value={'path':str(scaffold),'template_id':'generic','content':content}), patch.object(main, 'architecture_gate_validate', return_value={'status':'pass'}), contextlib.redirect_stdout(capture):
                    with self.assertRaises(SystemExit) as finished:
                        main.main()
                    self.assertEqual(finished.exception.code, 0)
                main_result = json.loads(capture.getvalue())['self_check']
                for key in ('pass','fail','skip','notes'):
                    self.assertEqual(main_result[key], result['self_check'][key])
                self.assertEqual(main_result['auto_remediation_iterations'], 0)
