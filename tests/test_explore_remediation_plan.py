"""Configuration plans are admitted and exercised by the real consumer."""
import copy
import unittest
from scripts.explore import self_check
from scripts.lib.extraction.schema import validate_extraction
from scripts.lib.extraction.preprocessor import preprocess_html


class PlanTests(unittest.TestCase):
    def test_missing_lazyload_evidence(self):
        rules = {'selectors': {'content': '#body'}}
        original = copy.deepcopy(rules)
        issue = {'check': 'S5', 'status': 'fail', 'fixable_type': 'base64_residue', 'detail': 'original'}
        plan = self_check.plan_remediation(rules, [issue])
        self.assertFalse(plan['changed'])
        self.assertEqual(plan['unresolved'][0]['reason_code'], 'missing_evidence')
        self.assertEqual(plan['unresolved'][0]['issue'], issue)
        self.assertEqual(rules, original)
        self.assertEqual(validate_extraction(plan['extraction']), [])

    def test_all_issue_types_and_deterministic_batch(self):
        issues = [{'fixable_type': kind, 'detail': kind} for kind in sorted(self_check.FIXABLE_ISSUES)]
        original = {'selectors': {'content': '#body'}, 'cleanup': ['strip_edit_links']}
        before = copy.deepcopy(original)
        plan = self_check.plan_remediation(original, issues)
        self.assertEqual(validate_extraction(plan['extraction']), [])
        self.assertEqual(original, before)
        self.assertEqual(plan, self_check.plan_remediation(original, list(reversed(issues))))
        supported = {'space_normalization', 'link_resolution', 'image_wrapper', 'table_class_missing'}
        self.assertEqual({i['fixable_type'] for i in plan['applied']}, supported - {'link_resolution'})
        for kind in supported:
            self.assertTrue(self_check.plan_remediation({}, [{'fixable_type': kind}])['changed'])
        self.assertEqual({i['fixable_type'] for i in plan['unresolved']}, self_check.FIXABLE_ISSUES - supported)
        self.assertEqual(self_check.auto_remediate(original, issues), plan['extraction'])
        self.assertFalse(self_check.plan_remediation(plan['extraction'], issues)['changed'])
        plan['extraction']['selectors']['content'] = '#other'
        self.assertEqual(original, before)

    def test_invalid_input_retained(self):
        original = {'cleanup': ['existing_op'], 'text_normalization': ['existing_norm']}
        plan = self_check.plan_remediation(original, [{'fixable_type': 'image_wrapper'}])
        self.assertEqual(plan['extraction'], original)
        self.assertEqual(plan['unresolved'][0]['reason_code'], 'invalid_configuration')
        self.assertFalse(plan['changed'])

    def test_lazyload_consumer_existing_and_explicit_evidence(self):
        lazy = {'placeholder_pattern': 'data:image/', 'real_src_attr': 'data-original'}
        html = '<div id="body"><img src="data:image/gif;base64,x" data-original="https://example.org/image.png"></div>'
        for rules, evidence in [({'lazyload': dict(lazy, enabled=False)}, None), ({}, {'lazyload': lazy})]:
            with self.subTest(rules=rules):
                original = copy.deepcopy(rules)
                plan = self_check.plan_remediation(rules, [{'fixable_type': 'base64_residue'}], evidence)
                self.assertEqual(validate_extraction(plan['extraction']), [])
                self.assertEqual(plan['unresolved'], [])
                cleaned = preprocess_html(html, plan['extraction'])
                self.assertIn('src="https://example.org/image.png"', cleaned)
                self.assertNotIn('src="data:image/', cleaned)
                self.assertEqual(rules, original)
                self.assertNotIn('fix_lazyload_images', plan['extraction'].get('cleanup', []))

    def test_invalid_evidence_rejected(self):
        plan = self_check.plan_remediation({}, [{'fixable_type': 'base64_residue'}],
                                         {'lazyload': {'placeholder_pattern': 'x', 'real_src_attr': 'data-src', 'unknown': True}})
        self.assertFalse(plan['changed'])
        self.assertEqual(plan['extraction'], {})
        self.assertEqual(plan['unresolved'][0]['reason_code'], 'invalid_configuration')

    def test_supported_actions_reach_consumers(self):
        from scripts.lib.extraction.converter import apply_post_conversion_ops
        plan = self_check.plan_remediation({}, [{'fixable_type': kind} for kind in
                                               ['image_wrapper', 'table_class_missing', 'space_normalization']])
        html = '<p>KEEP</p><a href="file"><img src="https://example.org/a.png"></a><table class="infobox-table"><tr><td>REMOVE</td></tr></table>'
        cleaned = preprocess_html(html, plan['extraction'])
        self.assertIn('KEEP', cleaned)
        self.assertIn('<img', cleaned)
        self.assertNotIn('<a ', cleaned)
        self.assertNotIn('REMOVE', cleaned)
        self.assertEqual(apply_post_conversion_ops('word2word', plan['extraction']), 'word 2 word')
