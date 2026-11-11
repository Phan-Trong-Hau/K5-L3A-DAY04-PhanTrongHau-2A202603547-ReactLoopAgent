"""Run the unchanged core evaluator, saving each finished case for safe resumption."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'evals'))
from run_evals import run_case
from grading import summarize


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.part')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description='Full core eval with per-case checkpoints; no grading changes')
    parser.add_argument('--checkpoint', type=Path, default=ROOT / 'reports/cp6_checkpoint.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'eval_after.json')
    parser.add_argument('--resume', action='store_true')
    options = parser.parse_args()
    baseline = json.loads((ROOT / 'eval_before.json').read_text())
    config = baseline['config']
    if config['dataset'] != 'core':
        parser.error('This runner supports the core dataset only.')
    cases = json.loads((ROOT / 'evals/cases.json').read_text())
    paths = ['agent.py', 'providers.py', 'status_tools.py', 'evals/run_evals.py',
             'evals/cases.json', 'evals/scenarios.py', 'evals/grading.py', 'local/Modelfile',
             'fixtures/github.json', 'fixtures/cloudflare.json']
    endpoint = os.getenv('OPENAI_BASE_URL', 'http://localhost:11434/v1').rstrip('/')
    request = urllib.request.Request(endpoint.removesuffix('/v1') + '/api/show',
                                     data=json.dumps({'model': config['model']}).encode(),
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=10) as response:
        model = json.load(response)
    fingerprint = {
        'config': config,
        'sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        'endpoint': endpoint,
        'model_modelfile': model['modelfile'],
        'local_model': os.getenv('LOCAL_MODEL'),
        'provider_timeout': os.getenv('PROVIDER_TIMEOUT', '60'),
        # The agent includes the current UTC date in its system prompt.
        'utc_date': datetime.now(timezone.utc).date().isoformat(),
    }
    if options.resume:
        state = json.loads(options.checkpoint.read_text())
        if state['fingerprint'] != fingerprint:
            parser.error('Code/model/config/date changed; cannot combine this checkpoint with a new run.')
        results = state['cases']
        if [r['id'] for r in results] != [c['id'] for c in cases[:len(results)]]:
            parser.error('Checkpoint cases do not match the dataset prefix.')
    else:
        if options.checkpoint.exists() or options.output.exists():
            parser.error('Output/checkpoint already exists. Use --resume or choose other paths.')
        state = {'started_at': datetime.now().astimezone().isoformat(),
                 'fingerprint': fingerprint, 'cases': [], 'state': 'running'}
        results = state['cases']
        write_json(options.checkpoint, state)
    args = SimpleNamespace(**config, bonus=False)
    for case in cases[len(results):]:
        print(f"Đang chạy {case['id']} ({len(results)}/{len(cases)} đã lưu)", flush=True)
        item = run_case(case, args)
        results.append(item)
        state['updated_at'] = datetime.now().astimezone().isoformat()
        write_json(options.checkpoint, state)
        print(f"{item['id']}: {item['grade']['score']} ({item['grade']['status']}); checkpoint saved", flush=True)
    report = {'summary': summarize(results), 'config': config, 'cases': results}
    write_json(options.output, report)
    state['state'] = 'complete'
    write_json(options.checkpoint, state)
    print(json.dumps(report['summary'], ensure_ascii=False), flush=True)
    return 0 if report['summary']['score_0_100'] is not None else 1


if __name__ == '__main__':
    sys.exit(main())
