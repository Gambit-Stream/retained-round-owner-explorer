#!/usr/bin/env python3
"""Run unchanged fixture suites from fresh temporary copies, using only stdlib."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

CASES = (
    ('01-session', 'test_recovery', 7, {'FRAME_VARIANT': 'Frame'}),
    ('02-route', 'test_settlement', 9, {'MODEL_VARIANT': 'Router'}),
    ('03-export', 'test_reader', 16, {}),
    ('04-decision', 'test_cashout', 14, {}),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verbose', action='store_true',
                        help='show actual unittest output, including variable timing')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    total = 0
    all_ok = True
    for name, module, expected_count, selectors in CASES:
        environment = os.environ.copy()
        for key in ('FRAME_VARIANT', 'MODEL_VARIANT', 'NEGATIVE_CONTROL',
                    'PYTHONPATH', 'PYTHONHOME'):
            environment.pop(key, None)
        environment.update(selectors)
        with tempfile.TemporaryDirectory(prefix='wallet-fixture-') as temporary:
            working = Path(temporary) / name
            shutil.copytree(root / 'cases' / name, working,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            result = subprocess.run(
                [sys.executable, '-E', '-s', '-B', '-m', 'unittest', '-v', module],
                cwd=working, env=environment, capture_output=True, text=True)
        output = result.stdout + result.stderr
        count = re.search(r'^Ran (\d+) tests? in ', output, re.MULTILINE)
        observed = int(count.group(1)) if count else None
        ok = (result.returncode == 0 and observed == expected_count
              and re.search(r'^OK\s*$', output, re.MULTILINE) is not None)
        all_ok = all_ok and ok
        if observed is not None:
            total += observed
        print(f'{name}: {"PASS" if ok else "FAIL"} ({observed} tests)')
        if args.verbose or not ok:
            print(output, end='' if output.endswith('\n') else '\n')
            if not ok:
                print(f'Expected {expected_count} passing tests; subprocess exit {result.returncode}.')
    print(f'TOTAL: {"PASS" if all_ok else "FAIL"} ({total} tests)')
    return 0 if all_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
