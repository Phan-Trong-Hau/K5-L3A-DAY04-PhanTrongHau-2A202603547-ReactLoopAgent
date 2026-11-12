"""Read-only audit of core submission artifacts; does not claim LMS submission."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bonus', action='store_true', help='Kiểm tra cả 10 case bonus và điểm /15')
    options = parser.parse_args()
    errors = []
    def check(condition, label):
        print(('PASS' if condition else 'FAIL') + ': ' + label)
        if not condition:
            errors.append(label)
    required = ('agent.py', 'eval_before.json', 'eval_after.json', 'NOTES.md')
    for name in required:
        check((ROOT / name).is_file(), 'File bắt buộc ' + name)
    if errors:
        return 1
    reports = [json.loads((ROOT / f'eval_{version}.json').read_text()) for version in ('before', 'after')]
    expected = {c['id'] for c in json.loads((ROOT / 'evals/cases.json').read_text())}
    for version, report in zip(('before', 'after'), reports):
        cases = report['cases']
        check(len(cases) == len(expected) == 22 and {c['id'] for c in cases} == expected,
              f'{version}: đủ đúng 22 case')
        scores = [c['grade'].get('score') for c in cases]
        check(all(c['grade']['status'] == 'scored' and isinstance(s, (int, float))
                  for c, s in zip(cases, scores)), f'{version}: không có unscored')
        check(report['summary']['score_0_100'] is not None, f'{version}: điểm tổng khác null')
        if scores and all(isinstance(s, (int, float)) for s in scores):
            check(round(sum(scores) / len(scores), 2) == report['summary']['score_0_100'],
                  f'{version}: điểm tổng khớp case scores')
    check(reports[0]['config'] == reports[1]['config'], 'Hai cấu hình eval giống nhau')
    notes = (ROOT / 'NOTES.md').read_text()
    check(all(re.search(r'^## ' + str(n) + r'\.', notes, re.M) for n in range(1, 6)),
          'NOTES có đủ 5 mục')
    manifest = json.loads((ROOT / 'reports/cp6_run_manifest.json').read_text())
    core_source = (ROOT / 'agent.py').read_text()
    begin, end = '    # BEGIN BONUS DISPATCH\n', '    # END BONUS DISPATCH\n'
    if begin in core_source and end in core_source:
        prefix, tail = core_source.split(begin, 1)
        core_source = prefix + tail.split(end, 1)[1]
    check(all((hashlib.sha256(core_source.encode()).hexdigest() if p == 'agent.py'
               else hashlib.sha256((ROOT / p).read_bytes()).hexdigest()) == digest
              for p, digest in manifest['sha256'].items()),
          'Core (loại dispatcher bonus) và dữ liệu khớp bản đã eval CP6')
    for version in ('before', 'after'):
        check(hashlib.sha256((ROOT / f'eval_{version}.json').read_bytes()).hexdigest()
              == manifest[f'eval_{version}_sha256'], f'Giữ nguyên kết quả eval_{version}')
    if options.bonus:
        bonus_path = ROOT / 'eval_bonus.json'
        check(bonus_path.is_file(), 'Có eval_bonus.json')
        if bonus_path.is_file():
            bonus = json.loads(bonus_path.read_text())
            bonus_ids = {c['id'] for c in json.loads((ROOT / 'bonus/cases.json').read_text())}
            check(len(bonus['cases']) == len(bonus_ids) == 10
                  and {c['id'] for c in bonus['cases']} == bonus_ids, 'Đủ đúng 10 case bonus')
            scores = [c['grade'].get('score') for c in bonus['cases']]
            scored = all(c['grade']['status'] == 'scored' and isinstance(score, (int, float))
                         for c, score in zip(bonus['cases'], scores))
            check(scored, 'Bonus không có case unscored')
            total = bonus['summary']['score_0_100']
            check(total is not None, 'Bonus có điểm tổng')
            if scored and scores and total is not None:
                check(round(sum(scores) / len(scores), 2) == total, 'Điểm tổng bonus khớp case scores')
                check(round(total * .15, 2) == bonus['summary']['bonus_points_0_15'], 'Quy đổi bonus /15 đúng')
            bonus_manifest = json.loads((ROOT / 'reports/bonus_run_manifest.json').read_text())
            check(bonus['config'] == bonus_manifest['config'], 'Config bonus khớp manifest')
            check(all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                      for name, digest in bonus_manifest['sha256'].items()), 'Code/dataset bonus khớp bản đã eval')
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    check(not any(Path(p).name == '.env' for p in tracked if p), 'Không track file .env')
    pattern = re.compile(r'\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|AIza[A-Za-z0-9_-]{30,})')
    matches = []
    for name in tracked:
        path = ROOT / name
        if name and path.is_file():
            try:
                if pattern.search(path.read_text()):
                    matches.append(name)
            except UnicodeError:
                pass
    check(not matches, 'Không khớp các mẫu credential phổ biến trong file tracked (không phải bảo đảm tuyệt đối)')
    print('\nLMS và demo trực tiếp cần xác nhận riêng; script không chứng nhận đã nộp bài.')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
