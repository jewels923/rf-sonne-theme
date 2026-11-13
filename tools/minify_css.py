#!/usr/bin/env python3
"""Generate minified CSS twins for production enqueues.

Sources stay editable; the theme serves the .min.css twins.
Run from the theme root:  F:/Python/python.exe -X utf8 tools/minify_css.py
Requires npx csso-cli (npm registry mirror is configured globally).
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    ('main.css', 'main.min.css'),
    ('sonne.css', 'sonne.min.css'),
    ('assets/css/sonne-insights.css', 'assets/css/sonne-insights.min.css'),
    ('assets/css/sonne-fonts.css', 'assets/css/sonne-fonts.min.css'),
]


def main():
    npx = shutil.which('npx') or shutil.which('npx.cmd')
    if not npx:
        print('npx not found on PATH', file=sys.stderr)
        return 1
    failures = []
    for source, target in PAIRS:
        src = ROOT / source
        dst = ROOT / target
        if not src.exists():
            print('SKIP missing source', source)
            continue
        result = subprocess.run(
            [npx, '--yes', 'csso-cli', str(src), '--output', str(dst)],
            capture_output=True, text=True, timeout=180,
        )
        if result.returncode != 0 or not dst.exists():
            failures.append(source)
            print('FAIL', source, result.stderr[:300])
            continue
        raw = src.read_text(encoding='utf-8')
        mini = dst.read_text(encoding='utf-8')
        if mini.count('{') != mini.count('}'):
            failures.append(source)
            print('FAIL unbalanced braces', target)
            continue
        print(f'{source}: {len(raw.encode("utf-8"))} -> {len(mini.encode("utf-8"))} bytes '
              f'({100 - len(mini.encode("utf-8")) * 100 // max(1, len(raw.encode("utf-8")))}% smaller)')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
