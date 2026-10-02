"""Exercise the real checker with isolated manifests and executables."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EngineVersionCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'configs').mkdir()
        shutil.copy(ROOT / 'scripts/engine-version-check.sh', self.root / 'scripts')

    def executable(self, name, body):
        p = self.root / name
        p.write_text('#!/bin/sh\n' + body)
        p.chmod(0o755)
        return str(p)

    def check(self, cloak, timeout=1):
        good = self.executable('good', 'echo 0.4.7\n')
        engines = {
            'cloakbrowser': {'expected_version': '0.4.3', 'detection': {'managed_path': cloak, 'timeout_seconds': timeout}},
            'scrapling': {'expected_version': '0.4.7', 'detection': {'managed_path': good}},
        }
        (self.root / 'configs/engine-versions.json').write_text(json.dumps({'engines': engines}))
        env = dict(os.environ)
        env.pop('CLOAKBROWSER_MANAGED_ROOT', None)
        p = subprocess.run(['bash', 'scripts/engine-version-check.sh', '--json'], cwd=self.root,
                           env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 1, p.stderr)
        result = json.loads(p.stdout)
        self.assertFalse(result['all_ok'])
        self.assertEqual(len(result['engines']), 2)
        self.assertFalse(result['engines'][1]['needs_update'])
        return result['engines'][0]

    def test_missing_does_not_abort_other_engines(self):
        self.assertEqual(self.check(str(self.root / 'missing'))['status'], 'not_installed')

    def test_timeout_is_distinct_from_missing(self):
        executable = self.executable('slow', 'exec sleep 2\n')
        self.assertEqual(self.check(executable, timeout=0.05)['status'], 'inspection_timeout')

    def test_invalid_version_is_inspection_failure(self):
        executable = self.executable('bad', 'echo not-a-version\n')
        self.assertEqual(self.check(executable)['status'], 'version_parse_failed')

    def test_nonzero_import_is_not_missing_environment(self):
        executable = self.executable('broken', 'exit 1\n')
        self.assertEqual(self.check(executable)['status'], 'detect_failed')
