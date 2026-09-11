import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import yaml
from scripts.explore.strategy_lifecycle import bootstrap_draft
from scripts.explore.freeze import freeze


class StrategyLifecycleTests(unittest.TestCase):
    def test_bootstrap_does_not_copy_identity(self):
        source={'domain':'old.fandom.com','description':'Old Game 1.0','api':{'platform':'mediawiki','platform_variant':'fandom','base_url':'https://old.fandom.com/api.php','taxonomy':{'list_pages':{'Old':'Old'}}},'extraction':{'cleanup':['strip_edit_links'],'image_handling':{'base_url':'https://old.fandom.com'}},'structure':{'pages':[{'label':'Old Game'}]}}
        draft=bootstrap_draft(source,'https://new.fandom.com/wiki/New')
        self.assertEqual(draft['lifecycle']['status'],'draft')
        self.assertNotIn('Old',draft['description'])
        self.assertEqual(draft['api']['base_url'],'https://new.fandom.com/api.php')
        self.assertNotIn('taxonomy',draft['api'])
        self.assertEqual(draft['structure']['pages'],[])
        with self.assertRaises(ValueError):bootstrap_draft(source,'https://new.fandom.com',profile='unknown')

    def test_freeze_failure_preserves_files_and_success_records_frozen(self):
        with tempfile.TemporaryDirectory() as out:
            root=Path(out);folder=root/'sites/strategies/example.org';folder.mkdir(parents=True)
            registry=folder.parent/'registry.json';registry.write_text('{"entries":[]}')
            file=folder/'strategy.md'
            doc={'domain':'example.org','description':'Example','structure':{'pages':[],'entry_points':[]},'lifecycle':{'status':'draft'}}
            def write():file.write_text('---\n'+yaml.safe_dump(doc)+'---\n<!-- Bootstrapped -->\n')
            write();before=file.read_bytes();result=freeze(out,str(file))
            self.assertFalse(result['ok']);self.assertEqual(before,file.read_bytes());self.assertEqual(json.loads(registry.read_text())['entries'],[])
            doc['structure']={'pages':[{'id':'home','url_example':'https://example.org/','type':'home'}],'entry_points':['home']}
            doc['lifecycle']['review_evidence']='Reviewed target identity against local sample fixture'
            write();result=freeze(out,str(file));self.assertTrue(result['ok'],result)
            self.assertNotIn('Bootstrapped',file.read_text());self.assertEqual(len(json.loads(registry.read_text())['entries']),1)

    def test_publication_failure_rolls_back(self):
        with tempfile.TemporaryDirectory() as out:
            root=Path(out);folder=root/'sites/strategies/example.org';folder.mkdir(parents=True)
            registry=folder.parent/'registry.json';registry.write_text('{"entries":[]}')
            file=folder/'strategy.md';file.write_text('---\ndomain: example.org\ndescription: Example\nstructure:\n  pages: [{id: home, type: home, url_example: "https://example.org/"}]\n  entry_points: [home]\nlifecycle: {status: draft, review_evidence: reviewed}\n---\n')
            before=file.read_bytes()
            with patch('scripts.explore.freeze.os.replace',side_effect=OSError('disk error')):
                self.assertFalse(freeze(out,str(file))['ok'])
            self.assertEqual(before,file.read_bytes());self.assertEqual(json.loads(registry.read_text())['entries'],[])

    def test_registry_format_order_and_repeat_freeze(self):
        for indent, newline in [(4, '\n'), (2, '')]:
            with self.subTest(indent=indent), tempfile.TemporaryDirectory() as out:
                root = Path(out)
                folder = root / 'sites/strategies/example.org'
                folder.mkdir(parents=True)
                registry = folder.parent / 'registry.json'
                before = {'entries': [{'domain': 'first.org', 'extra': 1}, {'domain': 'example.org'}, {'domain': 'last.org', 'extra': 2}], 'version': 1}
                registry.write_text(json.dumps(before, indent=indent) + newline)
                file = folder / 'strategy.md'
                file.write_text('---\ndomain: example.org\ndescription: Example\nstructure:\n  pages: [{id: home, type: home, url_example: "https://example.org/"}]\n  entry_points: [home]\nlifecycle: {status: frozen}\n---\n')
                self.assertTrue(freeze(out, str(file))['ok'])
                data = json.loads(registry.read_text())
                self.assertEqual([e['domain'] for e in data['entries']], ['first.org', 'example.org', 'last.org'])
                self.assertEqual(data['entries'][0], before['entries'][0])
                self.assertEqual(data['entries'][2], before['entries'][2])
                self.assertEqual(registry.read_text(), json.dumps(data, indent=indent, ensure_ascii=False) + newline)
                frozen = registry.read_bytes()
                self.assertTrue(freeze(out, str(file))['ok'])
                self.assertEqual(registry.read_bytes(), frozen)
