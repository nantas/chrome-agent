"""Main loop uses real planner and retains failures for KI consumption."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('explore_main_under_test', Path(__file__).resolve().parents[1] / 'scripts/explore/main.py')
main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_module)

class MainRemediationTests(unittest.TestCase):
    def run_loop(self, kinds, sample_failure=False):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            failure_batches = [[{'check': 'S11', 'status': 'fail', 'fixable_type': kind, 'detail': 'original'}] for kind in kinds]
            probe = {'success_engine': 'offline', 'results': [], 'html_content': ''}
            scaffold = {'path': 'draft', 'template_id': 'mediawiki', 'content': '---\nextraction: {}\napi:\n  platform: mediawiki\n---\n'}
            args = ['main.py', directory, 'https://example.org', '--run-dir', directory, '--samples', '[{"title":"Test","url":"https://example.org"}]']
            with patch('sys.argv', args), patch.object(main_module, 'probe', return_value=probe), patch.object(main_module, 'discover', return_value=[]), patch.object(main_module, 'identify', return_value={}), patch.object(main_module, 'generate', return_value=scaffold), patch.object(main_module, 'convert', return_value=[{'ok': not sample_failure, 'title': 'Test', 'markdown': 'body', 'error':'challenge_page' if sample_failure else None}]) as convert, patch.object(main_module, 'run_checks', side_effect=failure_batches), patch.object(main_module, 'architecture_gate_validate', return_value={'status': 'fail'}), contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit) as exit:
                    main_module.main()
                self.assertEqual(exit.exception.code, 2)
            return json.loads(output.getvalue()), convert.call_count

    def test_unsupported_only_no_retry_and_retains_identity(self):
        result, count = self.run_loop(['relative_link'] * 3)
        self.assertEqual(count, 1)
        check = result['self_check']
        self.assertFalse(check['overall_pass'])
        self.assertEqual(check['fixable_failures'][0]['detail'], 'original')
        self.assertEqual(check['remediation'][0]['unresolved'][0]['reason_code'], 'unsupported_consumer')

    def test_changed_rechecks_then_stops_on_no_change(self):
        result, count = self.run_loop(['image_wrapper'] * 3)
        self.assertEqual(count, 2)
        self.assertEqual(result['self_check']['auto_remediation_iterations'], 1)
        self.assertFalse(result['self_check']['overall_pass'])
        self.assertEqual(result['self_check']['remediation'][-1]['unresolved'][0]['issue']['fixable_type'], 'image_wrapper')

    def test_maximum_two_updates(self):
        result, count = self.run_loop(['image_wrapper', 'space_normalization', 'table_class_missing'])
        self.assertEqual(count, 3)
        self.assertEqual(result['self_check']['auto_remediation_iterations'], 2)

    def test_failed_samples_do_not_pass_empty_self_check(self):
        result, count = self.run_loop([], sample_failure=True)
        self.assertEqual(count, 1)
        self.assertEqual(result['result'], 'partial_success')
        self.assertFalse(result['self_check']['overall_pass'])
