"""Replay recorded eval evidence in the terminal; no model or network requests."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description='Demo trace đã ghi: không gọi model/API')
    parser.add_argument('--case', default='A8')
    parser.add_argument('--version', choices=['before', 'after', 'both', 'bonus'], default='both')
    parser.add_argument('--summary-only', action='store_true', help='Chỉ hiện trace và điểm, bỏ answer')
    parser.add_argument('--full-trace', action='store_true', help='Hiện đầy đủ JSON trace')
    args = parser.parse_args()
    versions = ['before', 'after'] if args.version == 'both' else [args.version]
    print('REPLAY EVIDENCE ĐÃ LƯU — không phải lần chạy model mới.')
    for version in versions:
        path = ROOT / f'eval_{version}.json'
        if not path.exists():
            parser.error(f'Chưa có file {path.name}; cần hoàn tất eval tương ứng trước.')
        report = json.loads(path.read_text(encoding='utf-8'))
        case = next((c for c in report['cases'] if c['id'] == args.case.upper()), None)
        if case is None:
            parser.error(f'Không có case {args.case} trong {path.name}')
        result, grade = case['result'], case['grade']
        print(f"\n{path.name} / {case['id']} / status={result['status']} / score={grade['score']}")
        print('Câu hỏi:', case['question'])
        print('Model calls:', len(result['usage']))
        if args.full_trace:
            print(json.dumps(result['trace'], ensure_ascii=False, indent=2))
        else:
            for event in result['trace']:
                label = f"Step {event.get('step', '?')} / {event['event']}"
                if event['event'] == 'tool':
                    observation = event['result']
                    evidence = {key: observation[key] for key in
                                ('provider', 'ok', 'error', 'id', 'status', 'overall', 'url', 'source', 'captured_at')
                                if key in observation}
                    print(label, event['name'], json.dumps(event['arguments'], ensure_ascii=False))
                    print('  Evidence:', json.dumps(evidence, ensure_ascii=False))
                else:
                    print(label, json.dumps({k: v for k, v in event.items() if k not in ('step', 'event')}, ensure_ascii=False))
        print('Mechanical checks:', json.dumps(grade.get('mechanical', {}), ensure_ascii=False))
        if not args.summary_only:
            print('\nAnswer:\n' + '\n'.join(line.rstrip() for line in result['answer'].splitlines()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
