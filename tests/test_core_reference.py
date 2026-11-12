"""Ensure the bonus dispatcher has not changed the evaluated core implementation."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CoreReferenceTests(unittest.TestCase):
    def test_core_implementation_and_eval_artifacts_are_preserved(self):
        source = (ROOT / 'agent.py').read_text()
        prefix, rest = source.split('    # BEGIN BONUS DISPATCH\n', 1)
        core = prefix + rest.split('    # END BONUS DISPATCH\n', 1)[1]
        manifest = json.loads((ROOT / 'reports/cp6_run_manifest.json').read_text())
        digest = hashlib.sha256(core.encode()).hexdigest()
        self.assertEqual(digest, manifest['sha256']['agent.py'])
        self.assertEqual(core.encode(), (ROOT / 'reports/reference/agent_cp6.py').read_bytes())
        for version in ('before', 'after'):
            self.assertEqual(hashlib.sha256((ROOT / f'eval_{version}.json').read_bytes()).hexdigest(),
                             manifest[f'eval_{version}_sha256'])
