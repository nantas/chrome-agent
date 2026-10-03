import copy
import unittest
from scripts.lib.extraction.schema import validate_extraction
from scripts.lib.extraction.converter import convert_page_full
from scripts.lib.extraction.preprocessor import preprocess_html
from scripts.explore.capability_gate import check_requirements

RULES = {'heading_normalization': [{'heading_selector': 'h3:has(.mw-headline)', 'label_selector': '.group'}]}
HTML = '<h3><span class="mw-headline" id="Group"><div style="display:none">Group</div></span></h3><div class="group"><b>Group</b></div><p>Body</p>'


class HeadingNormalizationTests(unittest.TestCase):
    def test_config_validation(self):
        self.assertEqual(validate_extraction(RULES), [])
        self.assertEqual(validate_extraction({}), [])
        self.assertEqual(validate_extraction({'heading_normalization': []}), [])
        for value in ({}, [None], [{'heading_selector': ''}], [{'heading_selector': '[', 'label_selector': '.g'}], [dict(RULES['heading_normalization'][0], extra=True)]):
            with self.subTest(value=value):
                self.assertTrue(validate_extraction({'heading_normalization': value}))
        self.assertEqual(check_requirements({'extraction': RULES}, {}), [])

    def test_pair_conversion_and_idempotence(self):
        clean = preprocess_html(HTML, RULES)
        self.assertEqual(clean, preprocess_html(clean, RULES))
        self.assertIn('id="Group"', clean)
        md = convert_page_full(HTML, RULES)
        self.assertEqual(md, '### **Group**\n\nBody')
        self.assertNotIn('Group', convert_page_full('<div style="display:none">Group</div>', RULES))

    def test_mismatch_and_nonadjacent_remain_unchanged(self):
        for html in [HTML.replace('<b>Group</b>', '<b>Other</b>'), HTML.replace('</h3>', '</h3><p>Gap</p>')]:
            self.assertEqual(preprocess_html(html, RULES), preprocess_html(html, {}))

    def test_source_audit_checks_level_and_does_not_accept_bold(self):
        from scripts.explore.self_check import run_checks, build_source_context
        context = build_source_context(HTML, RULES, input_scope='content_fragment')
        for md, expected in [('### **Group**\n\nBody', 'pass'), ('**Group**\n\nBody', 'fail'), ('## Group\n\nBody', 'fail'), ('Body', 'fail')]:
            with self.subTest(md=md):
                checks = run_checks(HTML, md, '', set(), source_context=context)
                self.assertEqual(next(c for c in checks if c['check'] == 'S8')['status'], expected)

    def test_audit_link_destinations_with_parentheses(self):
        from scripts.explore.self_check import run_checks, build_source_context
        html = '<h2><span class="mw-headline">Unique <a href="https://e.test/Item_(DLC)">Trinkets</a></span></h2>'
        md = convert_page_full(html, {})
        context = build_source_context(html, {}, input_scope='content_fragment')
        self.assertEqual(next(c for c in run_checks(html, md, '', set(), source_context=context) if c['check'] == 'S8')['status'], 'pass')

    def test_explicit_alias_preserves_visible_label_and_source_identity(self):
        rules = copy.deepcopy(RULES)
        rules['heading_normalization'][0]['label_aliases'] = {'Group': 'The Group'}
        html = HTML.replace('<b>Group</b>', '<b>The Group</b>')
        self.assertEqual(validate_extraction(rules), [])
        self.assertEqual(convert_page_full(html, rules), '### **The Group**\n\nBody')
        self.assertIn('id="Group"', preprocess_html(html, rules))
        from scripts.explore.self_check import run_checks, build_source_context
        context = build_source_context(html, rules, input_scope='content_fragment')
        self.assertEqual(next(c for c in run_checks(html, convert_page_full(html, rules), '', set(), source_context=context) if c['check'] == 'S8')['status'], 'pass')

    def test_dd2_and_kingdoms_group_fixtures(self):
        from scripts.explore.self_check import run_checks, build_source_context
        source = ['Creature Den', 'Cultist (Cosmic)', 'Fanatics', 'Fisherfolk', 'Lost Battalion', 'Plague Eaters', 'Swine', 'Slime', 'Gaunt', 'Pillager', 'Military', 'Shambler (Cosmic)', 'Death', 'The Collector']
        aliases = {'Cultist (Cosmic)': 'Cultist', 'Lost Battalion': 'The Lost Battalion', 'Plague Eaters': 'Plague Eaters (Gentry)', 'Shambler (Cosmic)': 'Shambler'}
        rules = copy.deepcopy(RULES)
        rules['heading_normalization'][0]['label_aliases'] = aliases
        for labels, count in [(source, 14), (['Beastman', 'Witch', 'Bloodsucker'], 3)]:
            html = ''.join('<h3><span class="mw-headline" id="g%s"><div style="display:none">%s</div></span></h3><div class="group"><a href="https://e.test/%s">%s</a><img src="https://e.test/%s.png"></div>' % (i, label, i, aliases.get(label, label), i) for i, label in enumerate(labels))
            md = convert_page_full(html, rules)
            self.assertEqual(sum(line.startswith('### ') for line in md.splitlines()), count)
            self.assertEqual(md.count('!['), count)
            self.assertEqual(preprocess_html(html, rules), preprocess_html(preprocess_html(html, rules), rules))
            context = build_source_context(html, rules, input_scope='content_fragment')
            self.assertEqual(next(c for c in run_checks(html, md, '', set(), source_context=context) if c['check'] == 'S8')['status'], 'pass')

    def test_normalized_heading_exposes_source_id_once(self):
        from bs4 import BeautifulSoup
        heading = BeautifulSoup(preprocess_html(HTML, RULES), 'html.parser')
        self.assertEqual(heading.h3.get('id'), 'Group')
        self.assertEqual(len(heading.select('[id="Group"]')), 1)
