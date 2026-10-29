#!/usr/bin/env python3
"""Fetch CSS/JS assets and image headers for the performance slice of the audit."""
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import certifi

HERE = Path(__file__).resolve().parent
CORPUS = json.loads((HERE / 'index.json').read_text(encoding='utf-8'))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'
CTX = ssl.create_default_context(cafile=certifi.where())
OPENER = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX))
ASSETS = HERE / 'assets'
ASSETS.mkdir(exist_ok=True)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def _open(url, headers, method='GET'):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'identity', **(headers or {})}, method=method)
    t0 = time.perf_counter()
    resp = OPENER.open(req, timeout=60)
    return resp, time.perf_counter() - t0


def fetch(url, retries=2):
    for attempt in range(retries + 1):
        try:
            resp, elapsed = _open(url, {})
            body = resp.read()
            return {'status': resp.status, 'body': body, 'headers': dict(resp.headers),
                    'ms': round(elapsed * 1000)}
        except urllib.error.HTTPError as exc:
            return {'status': exc.code, 'body': exc.read(), 'headers': dict(exc.headers or {}), 'ms': 0}
        except Exception as exc:  # noqa: BLE001
            if attempt == retries:
                return {'status': 0, 'body': b'', 'headers': {}, 'ms': 0, 'error': str(exc)}
            time.sleep(1.5)


def head(url, retries=1):
    for attempt in range(retries + 1):
        try:
            resp, elapsed = _open(url, {}, method='HEAD')
            return {'status': resp.status, 'headers': dict(resp.headers), 'ms': round(elapsed * 1000), 'bytes': 0}
        except urllib.error.HTTPError as exc:
            return {'status': exc.code, 'headers': dict(exc.headers or {}), 'ms': 0, 'bytes': 0}
        except Exception as exc:  # noqa: BLE001
            if attempt == retries:
                return {'status': 0, 'headers': {}, 'ms': 0, 'bytes': 0, 'error': str(exc)}
            time.sleep(1)


def absolute(u):
    return urllib.parse.urljoin('https://rf-sonne.com/', u.split('#')[0])


def tag_urls(tag_pattern, attr_pattern):
    urls = []
    for row in CORPUS:
        if not row['file'].endswith('.html'):
            continue
        html = (HERE / row['file']).read_text(encoding='utf-8', errors='replace')
        for tag in re.findall(tag_pattern, html, re.I):
            m = re.search(attr_pattern, tag, re.I)
            if m and not m.group(1).startswith(('data:', '#', 'mailto:', 'tel:')):
                urls.append(absolute(m.group(1)))
    return list(dict.fromkeys(urls))


def main():
    css = tag_urls(r'<link[^>]+>', r'href=["\']([^"\']+)["\']')
    css = [u for u in css if u.split('?')[0].endswith('.css')]
    js = tag_urls(r'<script[^>]*src=[^>]*>', r'src=["\']([^"\']+)["\']')
    imgs = tag_urls(r'<img\b[^>]*>', r'(?:data-src|src)=["\']([^"\']+)["\']')
    log('unique css', len(css), 'js', len(js), 'img', len(imgs))

    report = {'css': [], 'js': [], 'images': []}
    for kind, urls, save in (('css', css, True), ('js', js, True), ('images', imgs[:80], False)):
        for i, url in enumerate(urls, 1):
            res = head(url) if kind == 'images' else fetch(url)
            size = res.get('bytes') or len(res.get('body', b''))
            entry = {
                'url': url.split('?')[0],
                'query': urllib.parse.urlsplit(url).query,
                'status': res['status'],
                'bytes': int(res['headers'].get('Content-Length') or size or 0),
                'type': res['headers'].get('Content-Type', '').split(';')[0],
                'cache': res['headers'].get('Cache-Control', '') or res['headers'].get('x-hcdn-cache-status', ''),
                'ms': res['ms'],
            }
            report[kind].append(entry)
            body = res.get('body')
            if save and res['status'] == 200 and body:
                name = re.sub(r'[^A-Za-z0-9._-]+', '_', urllib.parse.urlsplit(url).path.strip('/')) or 'index'
                (ASSETS / name).write_bytes(body)
            log(kind, i, '/', len(urls), res['status'], entry['bytes'] // 1024, 'KB', entry['url'][:80])
            time.sleep(0.15)

    (HERE / 'assets.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    log('done')


if __name__ == '__main__':
    main()
