"""Exercise offline audit at the manifest/CLI boundary."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


class BatchAuditTests(unittest.TestCase):
    def test_real_manifest_context_coverage_and_safe_output(self):
        from scripts.explore.batch_audit import audit_manifest, write_report
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'a.html').write_text('<html><main><h2>Title</h2><p>Battle Config2fc</p><a href="https://e.test/b">Next</a></main></html>')
            (root/'a.md').write_text('## Title\n\nBattle Config2fc\n\n[Next](b.md)')
            manifest = {'extraction': {'selectors': {'content': 'main'}}, 'link_mapping': {'b.md': 'https://e.test/b'}, 'pages': [{'id': 'A', 'source_url': 'https://e.test/a', 'html_path': 'a.html', 'markdown_path': 'a.md', 'input_scope': 'full_document'}, {'id': 'Missing', 'html_path': 'missing', 'markdown_path': 'a.md', 'input_scope': 'full_document'}]}
            path = root/'manifest.json';path.write_text(json.dumps(manifest))
            with patch('urllib.request.urlopen', side_effect=AssertionError('network forbidden')):
                report = audit_manifest(path)
            self.assertEqual([p['id'] for p in report['pages']], ['A', 'Missing'])
            first = {c['check']: c for c in report['pages'][0]['checks']}
            self.assertEqual(first['S5']['status'], 'pass')
            self.assertTrue(first['S5']['notes'])
            self.assertEqual(first['S8']['status'], 'pass')
            self.assertTrue(report['pages'][1]['error'])
            self.assertFalse(report['complete_validation'])
            with self.assertRaises(ValueError):
                write_report(path, root/'a.md', report)
            self.assertTrue((root/'a.md').read_text().startswith('## Title'))
            cli = subprocess.run([sys.executable, '-m', 'scripts.explore.batch_audit', '--manifest', str(path), '--output', str(root/'report.json')], capture_output=True, text=True)
            self.assertEqual(cli.returncode, 2, cli.stderr)
            self.assertEqual(json.loads((root/'report.json').read_text())['coverage'], report['coverage'])

    def test_missing_scope_and_unmapped_local_links_are_explicit(self):
        from scripts.explore.batch_audit import audit_manifest
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'a.html').write_text('<main><p>Article</p></main>')
            (root/'a.md').write_text('[Article](unknown.md)')
            path = root/'manifest.json'
            path.write_text(json.dumps({'pages': [{'id': 'A', 'source_url': 'https://e.test/a', 'html_path': 'a.html', 'markdown_path': 'a.md'}]}))
            report = audit_manifest(path)
            checks = {c['check']: c for c in report['pages'][0]['checks']}
            self.assertEqual(checks['S1']['status'], 'skip')
            self.assertEqual(checks['S9']['status'], 'skip')
            self.assertEqual(report['pages'][0]['unresolved_links'], ['unknown.md'])
            self.assertFalse(report['complete_validation'])

    def test_encoded_parentheses_preserve_navigation_attribution(self):
        from scripts.explore.self_check import build_source_context, s9_navigation_leakage
        html = '<nav><a href="/wiki/Item_(DLC)">Item</a></nav><main><a href="/wiki/Item_(DLC)">Item</a></main>'
        context = build_source_context(html, {'selectors': {'content': 'main'}}, input_scope='full_document', source_url='https://e.test/wiki/Page')
        md = '[Item](https://e.test/wiki/Item_%28DLC%29) [Item](https://e.test/wiki/Item_%28DLC%29)'
        self.assertEqual(s9_navigation_leakage(md, context)['status'], 'skip')

    def test_source_url_is_required_for_attribution(self):
        from scripts.explore.batch_audit import audit_manifest
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'a.html').write_text('<p>Content</p>')
            (root/'a.md').write_text('Content')
            path = root/'manifest.json'
            path.write_text(json.dumps({'pages': [{'id': 'A', 'html_path': 'a.html', 'markdown_path': 'a.md', 'input_scope': 'content_fragment'}]}))
            self.assertEqual(audit_manifest(path)['input_errors'], 1)
