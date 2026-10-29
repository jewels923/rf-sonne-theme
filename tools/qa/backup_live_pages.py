#!/usr/bin/env python3
"""Back up all live WordPress pages and their raw content. Never prints secrets."""
import base64
import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'bak' / 'live-pages-2026-10-25'
SECRETS = json.loads((ROOT / 'w.secrets.json').read_text(encoding='utf-8'))
DOMAIN = 'https://rf-sonne.com'
USER = 'jewels923'
AUTH = 'Basic ' + base64.b64encode(f"{USER}:{SECRETS['app_password']}".encode()).decode()
CTX = ssl.create_default_context(cafile=certifi.where())


def get(path):
    request = urllib.request.Request(
        DOMAIN + path,
        headers={'Authorization': AUTH, 'Accept': 'application/json'},
    )
    with urllib.request.urlopen(request, timeout=60, context=CTX) as response:
        return response.status, json.loads(response.read())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pages = []
    page = 1
    while True:
        status, batch = get(f'/wp-json/wp/v2/pages?per_page=100&page={page}&context=edit')
        if status != 200:
            raise SystemExit(f'page fetch failed: {status}')
        if not batch:
            break
        pages.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    records = []
    for item in pages:
        slug = item.get('slug') or f"page-{item['id']}"
        content = (item.get('content') or {}).get('raw', '')
        (OUT / f'{slug}.html').write_text(content, encoding='utf-8')
        records.append({
            'id': item['id'],
            'slug': slug,
            'status': item.get('status'),
            'parent': item.get('parent'),
            'link': item.get('link'),
            'title': (item.get('title') or {}).get('raw', ''),
            'template': item.get('template', ''),
            'content_file': f'{slug}.html',
            'content_length': len(content),
        })

    (OUT / 'pages.json').write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(f'backed up {len(records)} pages to {OUT}')
    for record in sorted(records, key=lambda r: r['id']):
        print(f"{record['id']:4} {record['status']:9} {record['slug']:35} {record['content_length']}")


if __name__ == '__main__':
    main()
