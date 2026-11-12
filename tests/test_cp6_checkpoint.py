"""Resume tests for the checkpoint harness; no real LLM or status requests."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'local'))
import run_checkpoint_evals as runner


class CheckpointRunnerTests(unittest.TestCase):
    def prepare(self, root):
        config = {'provider': 'openai', 'model': 'local', 'judge_provider': 'openai',
                  'judge_model': 'local', 'max_steps': 8, 'dataset': 'core'}
        (root / 'evals').mkdir()
        (root / 'fixtures').mkdir()
        (root / 'local').mkdir()
        for name in ('agent.py', 'providers.py', 'status_tools.py', 'evals/run_evals.py',
                     'evals/scenarios.py', 'evals/grading.py', 'local/Modelfile',
                     'fixtures/github.json', 'fixtures/cloudflare.json'):
            (root / name).write_text('unchanged')
        (root / 'eval_before.json').write_text(json.dumps({'config': config}))
        (root / 'evals/cases.json').write_text(json.dumps([{'id': 'E1'}, {'id': 'E2'}]))
        return config

    def execute(self, root, responses, resume=False, bonus=False):
        argv = ['run_checkpoint_evals.py'] + (['--resume'] if resume else []) + (['--bonus'] if bonus else [])
        with patch.object(runner, 'ROOT', root), patch.object(sys, 'argv', argv), \
             patch.object(runner, 'run_case', side_effect=responses) as call, \
             patch.object(runner.urllib.request, 'urlopen',
                          side_effect=lambda *a, **k: io.BytesIO(b'{"modelfile":"FROM local"}')), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = runner.main()
        return code, call

    def item(self, case_id, score):
        return {'id': case_id, 'grade': {'score': score, 'status': 'scored'}}

    def test_interrupted_run_keeps_case_and_resume_runs_remaining_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.prepare(root)
            with self.assertRaises(KeyboardInterrupt):
                self.execute(root, [self.item('E1', 60), KeyboardInterrupt()])
            checkpoint = json.loads((root / 'reports/cp6_checkpoint.json').read_text())
            self.assertEqual([c['id'] for c in checkpoint['cases']], ['E1'])
            self.assertFalse((root / 'eval_after.json').exists())
            code, call = self.execute(root, [self.item('E2', 100)], resume=True)
            self.assertEqual(code, 0)
            self.assertEqual(call.call_count, 1)
            self.assertEqual(call.call_args.args[0]['id'], 'E2')
            report = json.loads((root / 'eval_after.json').read_text())
            self.assertEqual(report['config'], config)
            self.assertEqual(report['summary']['score_0_100'], 80)
            self.assertEqual([c['id'] for c in report['cases']], ['E1', 'E2'])

    def test_resume_rejects_changed_agent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root)
            with self.assertRaises(KeyboardInterrupt):
                self.execute(root, [self.item('E1', 60), KeyboardInterrupt()])
            (root / 'agent.py').write_text('changed')
            with self.assertRaises(SystemExit) as error:
                self.execute(root, [], resume=True)
            self.assertEqual(error.exception.code, 2)
            self.assertFalse((root / 'eval_after.json').exists())

    def test_fresh_run_cannot_overwrite_existing_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root)
            with self.assertRaises(KeyboardInterrupt):
                self.execute(root, [self.item('E1', 60), KeyboardInterrupt()])
            saved = (root / 'reports/cp6_checkpoint.json').read_bytes()
            with self.assertRaises(SystemExit):
                self.execute(root, [])
            self.assertEqual((root / 'reports/cp6_checkpoint.json').read_bytes(), saved)


    def test_bonus_run_uses_full_dataset_and_standard_bonus_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root)
            (root / 'bonus/fixtures').mkdir(parents=True)
            for name in ('bonus/agent.py', 'bonus/tools.py', 'bonus/fixtures/vercel.json'):
                (root / name).write_text('unchanged')
            (root / 'bonus/cases.json').write_text(json.dumps([{'id': f'B{i}'} for i in range(1, 11)]))
            code, calls = self.execute(root, lambda case, args: self.item(case['id'], 80), bonus=True)
            self.assertEqual(code, 0)
            self.assertEqual(calls.call_count, 10)
            report = json.loads((root / 'eval_bonus.json').read_text())
            self.assertEqual(report['config']['dataset'], 'bonus')
            self.assertEqual(report['config']['max_steps'], 16)
            self.assertEqual(report['summary']['bonus_points_0_15'], 12)
            self.assertTrue(calls.call_args.args[1].bonus)
            self.assertEqual(len(json.loads((root / 'reports/bonus_checkpoint.json').read_text())['cases']), 10)
