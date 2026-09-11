import argparse
import copy
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from scripts.explore.page_discovery import discover_pages
from scripts.explore.discovery_allpages import run_allpages_discovery
from scripts.explore.discovery import AllPagesDiscoveryStrategy


class FakeDiscovery(AllPagesDiscoveryStrategy):
    def discover_pages(self, *args):
        return [{'title':'Other','ns':0}, {'title':'Tools','ns':0}, {'title':'Category:Tools','ns':14}, {'title':'Slay the Spire 2:Other','ns':3000}]
    def discover_categories(self, *args): return {}
    def fetch_list_pages(self, *args): return {'Tools':'real body', 'Missing':'detached'}


class DiscoveryContractTests(unittest.TestCase):
    def setUp(self):
        self.strategy={'domain':'example.org','api':{'base_url':'https://example.org/api.php','taxonomy':{'list_pages':{'Tools':'Tools','Missing':'Missing'}}}}
        self.args=argparse.Namespace(exclude_category=[],max_pages=None,concurrency=None)

    def test_allpages_misc_and_namespace_preserved(self):
        m=run_allpages_discovery(None,self.strategy,'',FakeDiscovery())
        self.assertEqual([p['target_directory'] for p in m['pages']], ['Misc','Tools','Tools','Slay_the_Spire_2'])
        self.assertTrue(m['pages'][1]['is_list_page'])

    def test_real_assembly_keeps_body_and_list_links(self):
        from scripts.pipeline.pipeline.phases.assemble import run_assemble
        from scripts.lib.extraction.converter import HtmlToMarkdownConverter
        from unittest.mock import Mock
        pages=[{'title':'Tools','ns':0,'target_directory':'Tools','target_filename':'Tools.md','is_list_page':True},
               {'title':'Hammer','ns':0,'target_directory':'Tools','target_filename':'Hammer.md','is_list_page':False}]
        converter=HtmlToMarkdownConverter('example.org');converter.build_link_index(pages)
        link=converter.convert('<a href="/wiki/Tools">Tools</a>', source_dir='Tools')
        self.assertEqual(link, '[Tools](index.md)')
        from scripts.pipeline.strategies import ShortNameLinkResolver, ExactTitleLinkResolver
        for resolver in (ShortNameLinkResolver(), ExactTitleLinkResolver()):
            self.assertEqual(resolver.resolve('Tools','Tools','Tools',pages), '[Tools](index.md)')
        with tempfile.TemporaryDirectory() as out:
            run_assemble(out,{'pages':pages},{'Tools':{'status':'ok','content':'# Real tools guide'},'Hammer':{'status':'ok','content':link}},self.strategy,'example.org',Mock(),Mock())
            self.assertIn('Real tools guide',(Path(out)/'Tools/index.md').read_text())
            self.assertNotIn('(Tools.md)',(Path(out)/'Tools/index.md').read_text())
            self.assertTrue((Path(out)/'Tools/Hammer.md').exists())

    def test_canonical_list_title_is_resolved_without_expanding_scope(self):
        strategy={'domain':'example.org','api':{'base_url':'https://example.org/api.php','taxonomy':{'list_pages':{'Tools_List':'Tools','Redirected':'Tools'}}}}
        m={'pages':[{'title':'Tools List','ns':0,'target_directory':'Tools','target_filename':'Tools_List.md'}]}
        class Client:
            def parse(self, **kwargs): return {'parse':{'title':'Tools List'}}
        with tempfile.TemporaryDirectory() as out, patch('scripts.explore.page_discovery.build_pipeline'), patch('scripts.explore.page_discovery.run_allpages_discovery',return_value=m):
            discover_pages(strategy,out,self.args,client=Client())
            import json
            saved=json.loads((Path(out)/'page_manifest.json').read_text())
            self.assertEqual(saved['list_page_decisions']['Tools_List']['canonical_title'],'Tools List')
            self.assertEqual(saved['list_page_decisions']['Redirected']['canonical_title'],'Tools List')
            self.assertTrue(saved['pages'][0]['is_list_page']);self.assertEqual(len(saved['pages']),1)

    def test_public_discovery_publishes_eligible_v2_and_routes(self):
        m={'pages':[{'title':'Tools','ns':0,'target_directory':'Tools','target_filename':'Tools.md'}], 'list_page_content':{'Missing':'detached'}}
        with tempfile.TemporaryDirectory() as out, patch('scripts.explore.page_discovery.build_pipeline'), patch('scripts.explore.page_discovery.run_allpages_discovery',return_value=copy.deepcopy(m)) as allpages, patch('scripts.explore.page_discovery.run_homepage_discovery',return_value=copy.deepcopy(m)) as homepage:
            result=discover_pages(self.strategy,out,self.args,client=object())
            import json
            manifest=json.loads((Path(out)/'page_manifest.json').read_text())
            self.assertEqual(manifest['schema_version'],2)
            self.assertTrue(manifest['pages'][0]['is_list_page'])
            self.assertEqual(manifest['list_page_decisions']['Missing']['reason'],'absent_from_manifest')
            self.assertEqual(len(manifest['pages']),1)
            allpages.assert_called_once();homepage.assert_not_called()
            strategy=copy.deepcopy(self.strategy);strategy['api']['homepage']={'url':'/'}
            discover_pages(strategy,out,self.args,client=object());homepage.assert_called_once()


if __name__=='__main__':unittest.main()

class SummaryEvidenceTests(unittest.TestCase):
    def test_unknown_counts_and_index_agreement(self):
        from scripts.explore.page_discovery import build_summary
        m={'pages':[{'title':'A','target_directory':'Misc','is_list_page':False},{'title':'Tools','target_directory':'Tools','is_list_page':True}], 'list_page_decisions':{}}
        summary=build_summary(m, 0.2)
        self.assertEqual(summary['total_pages'],2)
        self.assertIsNone(summary['excluded']['total'])
        self.assertIsNone(summary['failure_rate'])
        self.assertEqual(summary['manifest_path'],'page_manifest.json')
        self.assertEqual(summary['categories']['Tools']['index_kind'],'real')
        self.assertEqual(summary['categories']['Misc']['index_kind'],'generated')
    def test_empty_discovery_is_failure(self):
        args=argparse.Namespace(exclude_category=[],max_pages=None,concurrency=None)
        strategy={'domain':'example.org','api':{'base_url':'https://example.org/api.php'}}
        with tempfile.TemporaryDirectory() as out, patch('scripts.explore.page_discovery.build_pipeline'), patch('scripts.explore.page_discovery.run_allpages_discovery',return_value={'pages':[]}):
            result=discover_pages(strategy,out,args,client=object())
            self.assertEqual(result['result'],'failure')
            self.assertFalse((Path(out)/'page_manifest.json').exists())
