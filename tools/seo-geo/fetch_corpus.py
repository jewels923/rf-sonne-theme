#!/usr/bin/env python3
"""Fetch the full rf-sonne.com corpus with the Hostinger bypass cookie.

Writes HTML + a timing/header index for the SEO/GEO audit.
Never prints credentials or the bypass code.
"""
import base64
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

import certifi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SECRETS = json.loads((ROOT / 'w.secrets.json').read_text(encoding='utf-8'))
DOMAIN = 'https://rf-sonne.com'
USER = 'jewels923'
AUTH = 'Basic ' + base64.b64encode(
    f"{USER}:{SECRETS['app_password']}".encode()).decode()
CTX = ssl.create_default_context(cafile=certifi.where())
JAR = CookieJar()
OPENER = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=CTX),
    urllib.request.HTTPCookieProcessor(JAR),
)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'
HTML_DIR = HERE / 'html'
HTML_DIR.mkdir(parents=True, exist_ok=True)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def raw(url, headers=None, timeout=90):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'identity', **(headers or {})})
    t0 = time.perf_counter()
    try:
        resp = OPENER.open(req, timeout=timeout)
        ttfbyte = time.perf_counter()
        body = resp.read()
        return {
            'status': resp.status, 'body': body,
            'ttfb': ttfbyte - t0, 'total': time.perf_counter() - t0,
            'headers': dict(resp.headers), 'final_url': resp.geturl(),
        }
    except urllib.error.HTTPError as exc:
        return {
            'status': exc.code, 'body': exc.read(),
            'ttfb': time.perf_counter() - t0, 'total': time.perf_counter() - t0,
            'headers': dict(exc.headers or {}), 'final_url': url,
        }


def fetch(url, retries=2):
    last = None
    for attempt in range(retries + 1):
        try:
            res = raw(url)
            if res['status'] < 500:
                return res
            last = res
        except Exception as exc:  # noqa: BLE001 - network layer
            last = {'status': 0, 'body': b'', 'ttfb': 0, 'total': 0, 'headers': {}, 'final_url': url, 'error': str(exc)}
        time.sleep(1.5 * (attempt + 1))
    return last


def find_key(value, key):
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for item in value.values():
            found = find_key(item, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_key(item, key)
            if found is not None:
                return found
    return None


def establish_bypass():
    res = raw(f'{DOMAIN}/wp-json/hostinger-tools-plugin/v1/get-settings',
              headers={'Authorization': AUTH})
    if res['status'] != 200:
        raise RuntimeError('bypass settings HTTP %s' % res['status'])
    code = find_key(json.loads(res['body']), 'bypass_code')
    if not code:
        raise RuntimeError('bypass code missing')
    raw(f'{DOMAIN}/?bypass_code={urllib.parse.quote(code)}')
    log('bypass established')


LOC = re.compile(r'<loc>\s*([^<\s]+)\s*</loc>', re.I)


def sitemap_urls():
    urls = []
    res = fetch(f'{DOMAIN}/sitemap_index.xml')
    if res['status'] != 200:
        log('sitemap_index HTTP', res['status'])
        return urls
    children = LOC.findall(res['body'].decode('utf-8', 'replace'))
    for child in children:
        sub = fetch(child)
        if sub['status'] != 200:
            log('sub-sitemap HTTP', sub['status'], child)
            continue
        urls.extend(LOC.findall(sub['body'].decode('utf-8', 'replace')))
        log('sitemap', child.rsplit('/', 1)[-1], len(LOC.findall(sub['body'].decode('utf-8', 'replace'))))
    return urls


def safe_name(url):
    path = urllib.parse.urlsplit(url).path.strip('/')
    return path.replace('/', '__') or 'home'


def title_of(html):
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S | re.I)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''


def main():
    establish_bypass()
    urls = sitemap_urls()
    for extra in ('/', '/robots.txt', '/llms.txt'):
        urls.append(DOMAIN + extra)
    seen, ordered = set(), []
    for url in urls:
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    log('total urls', len(ordered))

    index = []
    for i, url in enumerate(ordered, 1):
        res = fetch(url)
        body = res['body']
        is_html = 'text/html' in res['headers'].get('Content-Type', '') or url.rstrip('/') == DOMAIN
        name = safe_name(url) + ('.html' if is_html else '.txt')
        if body:
            (HTML_DIR / name).write_bytes(body)
        text = body.decode('utf-8', 'replace') if is_html else ''
        index.append({
            'url': url,
            'file': f'html/{name}',
            'status': res['status'],
            'final_url': res['final_url'],
            'ttfb_ms': round(res.get('ttfb', 0) * 1000),
            'total_ms': round(res.get('total', 0) * 1000),
            'bytes': len(body),
            'cache': res['headers'].get('x-hcdn-cache-status') or res['headers'].get('X-Hcdn-Cache-Status', ''),
            'encoding': res['headers'].get('Content-Encoding', ''),
            'title': title_of(text),
        })
        log('%3d/%d %s %s %dKB %dms' % (i, len(ordered), res['status'], safe_name(url)[:44], len(body) // 1024, index[-1]['ttfb_ms']))
        time.sleep(0.3)

    (HERE / 'index.json').write_text(json.dumps(index, indent=1, ensure_ascii=False), encoding='utf-8')
    ok = sum(1 for r in index if r['status'] == 200)
    log('done: %d urls, %d ok, %d non-200' % (len(index), ok, len(index) - ok))


if __name__ == '__main__':
    main()
