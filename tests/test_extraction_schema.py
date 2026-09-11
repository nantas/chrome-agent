import unittest
from scripts.lib.extraction.schema import validate_extraction
from scripts.explore.architecture_gate import validate


class ExtractionSchemaTests(unittest.TestCase):
    def test_malformed_cleanup_and_normalization(self):
        for config in [{'cleanup':[{'strip_toc':'remove'}]}, {'cleanup':'strip_toc'}, {'text_normalization':{'space_fix':True}}, {'cleanup':['not_an_op']}, {'pipeline':'description'}, {'totally_unknown_field':True}, {'lazyload':{'enabled':True,'unknown':1}}]:
            with self.subTest(config=config):
                self.assertTrue(validate_extraction(config))
                result=validate([],[],config,'article','example.org')
                self.assertEqual(result['status'],'fail')
                self.assertTrue(result['schema_errors'])

    def test_supported_shared_configuration(self):
        self.assertEqual(validate_extraction({'cleanup':['strip_edit_links','fix_separators'], 'text_normalization':['fix_spaces'], 'lazyload':{'enabled':True,'placeholder_pattern':'data:', 'real_src_attr':'data-src'}}),[])


if __name__=='__main__':unittest.main()

class FandomMigrationTests(unittest.TestCase):
    def test_neon_schema_and_real_cleanup(self):
        from scripts.lib.strategy_loader import parse_strategy
        from scripts.lib.extraction.preprocessor import preprocess_html
        from scripts.lib.extraction.converter import apply_post_conversion_ops
        rules=parse_strategy('sites/strategies/neonabyss.fandom.com/strategy.md')['extraction']
        self.assertEqual(validate_extraction(rules),[])
        html='<div class="mw-parser-output"><span class="mw-editsection">EDIT</span><div id="toc">TOC</div><img src="data:image/gif;base64,abc" data-src="https://example.org/a.png"><table class="ambox"><tr><td>NOTICE</td></tr></table></div>'
        cleaned=preprocess_html(html,rules)
        self.assertNotIn('EDIT',cleaned);self.assertNotIn('TOC',cleaned)
        self.assertIn('src="https://example.org/a.png"',cleaned)
        self.assertIn('⚠️ NOTICE',cleaned)
        self.assertEqual(apply_post_conversion_ops('Version1.2Test',rules),'Version 1.2 Test')
    def test_fandom_template_schema(self):
        from scripts.lib.strategy_loader import parse_strategy
        self.assertEqual(validate_extraction(parse_strategy('sites/templates/mediawiki-fandom.yaml')['extraction']),[])


class ExistingMediawikiMigrationTests(unittest.TestCase):
    def test_noop_cleanup_migration_preserves_kernel_output(self):
        import copy
        from pathlib import Path
        from scripts.lib.strategy_loader import parse_strategy
        from scripts.lib.extraction.converter import convert_html_to_markdown
        from scripts.lib.extraction.preprocessor import _preprocess_explore
        html='<div><p>Stable body</p><span class="mw-editsection">edit</span><p><a href="/wiki/Other">Other</a></p></div>'
        for domain in ['slaythespire.wiki.gg','balatrowiki.org','bindingofisaacrebirth.wiki.gg','vampire.survivors.wiki']:
            rules=parse_strategy(str(Path('sites/strategies')/domain/'strategy.md'))['extraction']
            self.assertEqual(validate_extraction(rules),[],domain)
            old=copy.deepcopy(rules);old['cleanup']+=['normalize_infobox','strip_dpl_wikitext','strip_json_data']
            self.assertEqual(_preprocess_explore(html,old),_preprocess_explore(html,rules))
    def test_non_mediawiki_descriptive_cleanup_is_not_mediawiki_schema(self):
        from scripts.explore.strategy_lifecycle import validate_target
        validate_target({'domain':'example.org','description':'Static site','structure':{'pages':[{'id':'home','url_example':'https://example.org/'}],'entry_points':['home']},'extraction':{'cleanup':['Remove promotional content']}})

class GateSharedDefaultsTests(unittest.TestCase):
    def test_fandom_template_and_neon_pass_full_gate(self):
        from scripts.lib.strategy_loader import parse_strategy
        for file in ['sites/templates/mediawiki-fandom.yaml','sites/strategies/neonabyss.fandom.com/strategy.md']:
            strategy=parse_strategy(file)
            result=validate([],[],strategy['extraction'],'article',strategy.get('domain',''))
            self.assertEqual(result['status'],'pass',result)
