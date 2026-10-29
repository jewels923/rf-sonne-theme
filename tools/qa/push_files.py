#!/usr/bin/env python3
"""Upload theme files through trans.php using base64 bodies.

The host WAF rejects raw payloads containing PHP superglobals (HTTP 403),
so every file is sent base64-encoded. Credentials come from w.py / w.secrets.json
and are never printed.

Usage: python bak/qa/push_files.py <relative-path> [...]
"""

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import w  # noqa: E402


def push(rel, backup=True):
    local = ROOT / rel
    data = local.read_bytes()
    payload = {
        'action': 'write_file',
        'path': './' + rel,
        'content': base64.b64encode(data).decode('ascii'),
        'encoding': 'base64',
        'backup': backup,
    }
    result = w.sync_request(payload)
    remote = result['data']['bytes']
    if remote != len(data):
        raise SystemExit('size mismatch for %s: local %d remote %d' % (rel, len(data), remote))
    print('OK   %s (%d bytes)' % (rel, remote))


def main():
    files = sys.argv[1:]
    if not files:
        raise SystemExit('usage: python bak/qa/push_files.py <relative-path> [...]')
    for rel in files:
        push(rel)


if __name__ == '__main__':
    main()
