#!/usr/bin/env python3
"""Back up live HTML/CSS before the sitewide overlay-caption rollout. Never prints secrets."""
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blog_setup

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'bak' / 'live-2026-10-27-overlay-all'
ROUTES = json.loads((ROOT / 'bak' / 'qa-2026-10-27-overlay-all' / 'routes.json').read_text(encoding='utf-8'))
MODIFIED = {
    path.stem
    for path in (ROOT / 'website').glob('*.html')
    if '<figcaption' in path.read_text(encoding='utf-8') and path.stem != 'home'
}


def main():
    blog_setup.establish_bypass()
    OUT.mkdir(parents=True, exist_ok=True)
    report = []
    for slug, route in ROUTES:
        if slug not in MODIFIED:
            continue
        url = 'https://rf-sonne.com' + route + '/'
        status, _, body = blog_setup.request(url)
        text = body.decode('utf-8', 'replace')
        report.append({
            'slug': slug,
            'status': status,
            'bytes': len(body),
            'marker': bool(re.search(r'class="sn-[a-z0-9-]+', text)),
        })
        if status == 200:
            (OUT / f'{slug}.html').write_bytes(body)
    status, _, css = blog_setup.request(
        'https://rf-sonne.com/wp-content/themes/generatepress-child/sonne.css'
    )
    if status == 200:
        (OUT / 'sonne.css').write_bytes(css)
    report.append({'asset': 'sonne.css', 'status': status, 'bytes': len(css)})
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
