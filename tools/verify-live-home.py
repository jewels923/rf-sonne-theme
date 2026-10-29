#!/usr/bin/env python3
"""Live verification for the deployed SONNE homepage. Prints no secrets."""
import importlib.util
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.cookiejar import CookieJar
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('blog_setup', ROOT / 'bak' / 'qa' / 'blog_setup.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

DOMAIN = 'https://rf-sonne.com'
CTX = ssl.create_default_context(cafile=certifi.where())


def anon_request(url):
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=CTX),
        urllib.request.HTTPCookieProcessor(CookieJar()),
    )
    req = urllib.request.Request(url, headers={'Cache-Control': 'no-cache', 'Accept': 'text/html'})
    try:
        with opener.open(req, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read().decode('utf-8', 'replace')


def fetch(url):
    status, headers, body = m.request(url, headers={'Cache-Control': 'no-cache'})
    return status, headers, body.decode('utf-8', 'replace')


m.establish_bypass()
report = {}

status, headers, html = fetch(DOMAIN + '/')
report['root'] = {
    'status': status,
    'bytes': len(html),
    'title': re.search(r'<title>(.*?)</title>', html, re.S).group(1).strip() if re.search(r'<title>(.*?)</title>', html, re.S) else None,
    'cache': headers.get('x-cache') or headers.get('X-Cache') or headers.get('x-seraphinite-accelerator'),
    'server': headers.get('server'),
}
markers = {
    'new_rail': 'data-rail-track' in html,
    'trace_clip': 'data-trace-clip' in html,
    'inline_style': '.sn-home__plate-spec' in html,
    'inline_script': 'setProgress' in html,
    'old_five_cards': 'sn-home__card-grid' in html,
    'h1': len(re.findall(r'<h1[ >]', html, re.I)),
    'h1_text': re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', (re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S) or [None, ''])[1])).strip(),
    'main_tags': len(re.findall(r'<main[ >]', html, re.I)),
    'faq_details': html.count('<details'),
    'phone': '+86-0574-63615958' in html,
    'address': 'No. 87, 89, 91, Sanbei Middle Road' in html,
    'noindex_meta': bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', html, re.I)),
    'x_robots': headers.get('x-robots-tag'),
}
report['markers'] = markers

ld_blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I)
ld_types = []
ld_faq = None
ld_org = None
for block in ld_blocks:
    try:
        data = json.loads(block.strip())
    except json.JSONDecodeError as exc:
        ld_types.append('INVALID: %s' % exc)
        continue
    items = data if isinstance(data, list) else data.get('@graph', [data])
    for item in items:
        if not isinstance(item, dict):
            continue
        typ = item.get('@type')
        ld_types.append(typ)
        if typ == 'FAQPage':
            ld_faq = len(item.get('mainEntity', []))
        if typ == 'Organization':
            ld_org = {
                'phone': item.get('telephone'),
                'street': item.get('address', {}).get('streetAddress'),
                'city': item.get('address', {}).get('addressLocality'),
            }
report['jsonld'] = {'types': ld_types, 'faq_count': ld_faq, 'org': ld_org}

settings = m.api('/wp-json/wp/v2/settings')
report['settings'] = {k: settings.get(k) for k in ('blog_public', 'show_on_front', 'page_on_front', 'page_for_posts')}

anon_status, anon_headers, anon_html = anon_request(DOMAIN + '/')
report['anonymous'] = {
    'status': anon_status,
    'is_coming_soon': 'Custom RF &amp; Microwave Components' not in anon_html,
    'has_maintenance_hint': any(x in anon_html.lower() for x in ('coming soon', 'maintenance', 'hostinger')),
    'bytes': len(anon_html),
    'x_robots': anon_headers.get('x-robots-tag'),
}

# collect same-origin assets and links
def absolute(url):
    if not url:
        return None
    url = url.strip()
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return DOMAIN + url
    if url.startswith('http'):
        return url
    return urllib.parse.urljoin(DOMAIN + '/', url)


assets = set()
for tag in re.findall(r'<(?:img|script|link|source)\b[^>]*>', html, re.I):
    for attr in ('src', 'href'):
        mm = re.search(r'\b%s=["\']([^"\']+)["\']' % attr, tag, re.I)
        if mm:
            u = absolute(mm.group(1))
            if u and u.startswith(DOMAIN):
                assets.add(u)
for mm in re.finditer(r'\bsrcset=["\']([^"\']+)["\']', html, re.I):
    for part in mm.group(1).split(','):
        candidate = part.strip().split(' ')[0]
        u = absolute(candidate)
        if u and u.startswith(DOMAIN):
            assets.add(u)
assets = sorted(a for a in assets if not a.endswith(('#',)))

def check_asset(url):
    try:
        code, headers, body = fetch(url)
        return url, code, headers.get('content-type', ''), len(body)
    except Exception as exc:
        return url, 'ERR', str(exc)[:80], 0

with ThreadPoolExecutor(max_workers=6) as pool:
    asset_results = list(pool.map(check_asset, assets))
report['assets'] = {
    'total': len(asset_results),
    'bad': [r for r in asset_results if r[1] != 200],
    'types': sorted({re.sub(r';.*', '', r[2]) for r in asset_results if r[1] == 200}),
}

links = set()
for mm in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\']', html, re.I):
    href = mm.group(1).strip()
    if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
        continue
    u = absolute(href)
    if u and u.startswith(DOMAIN):
        links.add(u.split('#')[0])
links.discard(DOMAIN + '/')
links = sorted(links)

def check_link(url):
    try:
        code, headers, body = fetch(url)
        return url, code
    except Exception as exc:
        return url, 'ERR:%s' % str(exc)[:40]

with ThreadPoolExecutor(max_workers=6) as pool:
    link_results = list(pool.map(check_link, links))
report['links'] = {
    'total': len(link_results),
    'bad': [r for r in link_results if r[1] not in (200, 301, 302, 307, 308)],
}

print(json.dumps(report, indent=2, ensure_ascii=False))
