"""Run one local question and show the answer plus a compact execution trace."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import run


def main():
    parser = argparse.ArgumentParser(description='Thử Status Agent bằng Ollama local')
    parser.add_argument('question', nargs='?', help='Bỏ trống để nhập câu hỏi trong terminal')
    parser.add_argument('--mode', choices=['snapshot', 'live'], default='snapshot')
    parser.add_argument('--bonus', action='store_true', help='Dùng 5 providers và tools bonus')
    parser.add_argument('--max-steps', type=int, default=None)
    parser.add_argument('--output', type=Path, help='Lưu toàn bộ answer, trace và usage thành JSON')
    args = parser.parse_args()
    args.max_steps = args.max_steps if args.max_steps is not None else (16 if args.bonus else 6)
    if args.max_steps < 1:
        parser.error('--max-steps phải >= 1')
    try:
        question = args.question or input('Câu hỏi: ').strip()
    except (EOFError, KeyboardInterrupt):
        return 1
    if not question.strip():
        parser.error('Câu hỏi không được để trống')
    for name, value in {
        'OPENAI_BASE_URL': 'http://localhost:11434/v1',
        'OPENAI_API_KEY': 'local', 'LOCAL_MODEL': '1', 'PROVIDER_TIMEOUT': '300',
    }.items():
        os.environ.setdefault(name, value)
    print('Đang gọi model local; có thể mất vài phút...', flush=True)
    try:
        result = run(question, args.mode, 'openai', os.getenv('MODEL', 'status-agent-local'), args.max_steps, bonus=args.bonus)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f'Lỗi: {exc}', file=sys.stderr)
        return 1
    print(f"\nTrạng thái: {result['status']}\n\n{result['answer']}")
    print('\nTrace tóm tắt:')
    for event in result['trace']:
        if event['event'] == 'tool':
            print(f"  Step {event['step']}: {event['name']} {json.dumps(event['arguments'], ensure_ascii=False)}")
        else:
            print(f"  {json.dumps(event, ensure_ascii=False)}")
    if result.get('error'):
        print(f"Lỗi: {result['error']}", file=sys.stderr)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'\nĐã lưu JSON: {args.output}')
    return 0 if result['status'] == 'completed' else 1


if __name__ == '__main__':
    sys.exit(main())
