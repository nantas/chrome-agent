"""Wikitext scanner termination and document-order regression tests."""
import subprocess
import sys
import unittest
from scripts.pipeline.converters.wikitext_to_md import convert_wikitable_to_markdown

TABLE = '{|\n! Name\n|-\n| First\n|}'


class WikitableScanningTests(unittest.TestCase):
    def test_head_guard_detects_original_infinite_loop(self):
        # Run HEAD source in isolation; never change the user's patched worktree.
        source = subprocess.check_output(['git', 'show', 'd10858d:scripts/pipeline/converters/wikitext_to_md.py'], text=True)
        start = source.index('def convert_wikitable_to_markdown')
        end = source.index('\ndef _parse_wikitable_block', start)
        function = source[start:end]
        harness = 'from __future__ import annotations\nimport re\n' + function + '\n_parse_wikitable_block = lambda *a: "TABLE"\n'
        with self.assertRaises(subprocess.TimeoutExpired):
            subprocess.run([sys.executable, '-c', harness + 'convert_wikitable_to_markdown(' + repr(TABLE + '\nTail') + ', [], "")'], timeout=1, capture_output=True)
        result = subprocess.run([sys.executable, '-c', 'from scripts.pipeline.converters.wikitext_to_md import convert_wikitable_to_markdown as f; print(f(' + repr(TABLE + '\nTail') + ', [], ""))'], timeout=3, capture_output=True, text=True, check=True)
        self.assertIn('First', result.stdout)
        self.assertIn('Tail', result.stdout)

    def test_first_and_second_table_are_converted(self):
        text = TABLE + '\nBetween\n' + TABLE.replace('First', 'Second') + '\nTail'
        md = convert_wikitable_to_markdown(text, [], '')
        self.assertNotIn('{|', md)
        for word in ('First', 'Between', 'Second', 'Tail'):
            self.assertEqual(md.count(word), 1)
        self.assertLess(md.index('First'), md.index('Second'))

    def test_prose_and_unclosed_table_are_preserved(self):
        self.assertIn('Intro', convert_wikitable_to_markdown('Intro\n' + TABLE, [], ''))
        malformed = 'Intro\n{|\n| unfinished'
        self.assertEqual(convert_wikitable_to_markdown(malformed, [], ''), malformed)

    def test_multiple_cells_survive(self):
        md = convert_wikitable_to_markdown('{|\n! Name !! Value\n|-\n| First || Second\n|}', [], '')
        self.assertIn('First', md)
        self.assertIn('Second', md)

    def test_nested_table_scanner_terminates(self):
        nested = '{|\n! Outer\n|-\n| text\n{|\n! Inner\n|-\n| inner\n|}\n|}\nTail'
        result = convert_wikitable_to_markdown(nested, [], '')
        self.assertIn('Tail', result)
        self.assertIn('inner', result)
