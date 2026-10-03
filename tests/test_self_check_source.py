"""Source-aware quality checks through run_checks, independent of rendering."""
import unittest
from scripts.explore.self_check import run_checks


class SourceCheckTests(unittest.TestCase):
    def check(self, code, html, md, rules=None, scope='full_document'):
        from scripts.explore.self_check import build_source_context
        context = build_source_context(html, rules or {'selectors': {'content': 'main'}},
                                       input_scope=scope, source_url='https://example.org/wiki/Page')
        return next(r for r in run_checks(html, md, '', set(), source_context=context) if r['check'] == code)

    def test_s1_skin_excluded_but_missing_body_image_fails(self):
        html = '<img src="/skin.png"><main><img src="/body.png"></main>'
        md = '![](https://example.org/body.png)'
        self.assertEqual(self.check('S1', html, md)['status'], 'pass')
        self.assertEqual(self.check('S1', html, '')['status'], 'fail')
        self.assertEqual(self.check('S1', html, '![](https://example.org/other.png)')['status'], 'fail')

    def test_s1_fragment_infobox_overlap_filter_lazyload_and_balanced_urls(self):
        rules = {'selectors': {'content': 'main'}, 'infobox': {'enabled': True, 'selector': 'aside'},
                 'image_filtering': {'skip_patterns': ['decor']},
                 'lazyload': {'enabled': True, 'placeholder_pattern': 'data:', 'real_src_attr': 'data-src'}}
        html = '<aside><img src="/box.png"></aside><main><img src="/decor.png"><img src="data:x" data-src="/a_(b).png"><img src="/a_(b).png"></main>'
        md = '![](https://example.org/box.png) ![](https://example.org/a_(b).png) ![](https://example.org/a_(b).png)'
        self.assertEqual(self.check('S1', html, md, rules)['status'], 'pass')
        self.assertEqual(self.check('S1', html, md.rsplit(' ', 1)[0], rules)['status'], 'fail')
        self.assertEqual(self.check('S1', '<main><aside><img src="/box.png"></aside></main>', '![](https://example.org/box.png)', rules)['status'], 'pass')
        self.assertEqual(self.check('S1', '<img src="/x.png">', '![](https://example.org/x.png)', scope='content_fragment')['status'], 'pass')
        self.assertEqual(self.check('S1', '<p>No root</p>', '')['status'], 'fail')

    def test_s9_real_navigation_and_legitimate_topics(self):
        html = '<nav><a href="/login">Log in</a><a href="/register">Create account</a></nav><main><ul><li>Combat Items</li><li>Stagecoach Items</li><li>Inn Items</li></ul></main>'
        self.assertEqual(self.check('S9', html, 'Combat Items\nStagecoach Items\nInn Items')['status'], 'pass')
        self.assertEqual(self.check('S9', html, '[Log in](https://example.org/login)\n[Create account](https://example.org/register)')['status'], 'fail')

    def test_s9_body_collision_and_missing_evidence(self):
        html = '<nav><a href="/login">Log in</a><a href="/register">Create account</a></nav><main><a href="/login">Log in</a><a href="/wiki/Special:Help">Help</a></main>'
        self.assertNotEqual(self.check('S9', html, '[Log in](/login)\n[Help](/wiki/Special:Help)')['status'], 'fail')
        from scripts.explore.self_check import s9_navigation_leakage
        self.assertEqual(s9_navigation_leakage('Items\nItems\nItems')['status'], 'skip')

    def test_s5_source_typo_notes_and_new_occurrence_failure(self):
        html = '<main><p>hits both of <b>of</b> its ranks</p></main>'
        md = 'hits both of **of** its ranks'
        result = self.check('S5', html, md)
        self.assertEqual(result['status'], 'pass')
        self.assertTrue(result['notes'])
        self.assertEqual(self.check('S5', html, md + '\n\n' + md)['status'], 'fail')
        self.assertEqual(self.check('S5', '<main><p>hero</p></main>', 'hero hero')['status'], 'fail')

    def test_s5_notes_do_not_hide_other_failures_or_join_blocks(self):
        html = '<main><p>over over time</p><p>hero</p><p>hero</p></main>'
        self.assertEqual(self.check('S5', html, 'over over time\n\nhero\n\nhero')['status'], 'pass')
        self.assertEqual(self.check('S5', html, 'over over time </div>')['status'], 'fail')
        self.assertEqual(self.check('S5', '<main>Clean</main>', '[Clean](https://example.org/hero%20hero)\n`hero hero`')['status'], 'pass')
        from scripts.explore.self_check import s5_text_integrity
        self.assertEqual(s5_text_integrity('hero hero')['status'], 'skip')

    def test_s5_images_are_text_boundaries(self):
        html = '<main><p>2 <img src="/a.png"> 2 <img src="/b.png"> 2</p></main>'
        md = '2 ![](https://example.org/a.png) 2 ![](https://example.org/b.png) 2'
        result = self.check('S5', html, md)
        self.assertEqual(result['status'], 'pass')
        self.assertFalse(result['notes'])

    def test_invalid_scope_fails_and_legacy_scope_is_explicitly_unverified(self):
        self.assertEqual(self.check('S1', '<main>Body</main>', 'Body', {'selectors': {'content': '['}})['status'], 'fail')
        check = next(r for r in run_checks('<img src="/skin.png">', '', '', set()) if r['check'] == 'S1')
        self.assertEqual(check['status'], 'skip')
        self.assertIn('scope', check['detail'].lower())
