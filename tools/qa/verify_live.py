#!/usr/bin/env python3
"""Live verification for the SONNE P3 pages. Never prints secrets."""
import html
import importlib.util
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / 'bak' / '2026-10-25-p3-full'
sys.path.insert(0, str(ROOT / 'tests'))
import test_p3_pages as contract  # noqa: E402

spec = importlib.util.spec_from_file_location('bs', ROOT / 'bak' / 'qa' / 'blog_setup.py')
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)

DOMAIN = bs.DOMAIN
SYSTEM_TDK = {
    'thank-you': {
        'title': 'Thank You — Request Received | SONNE',
        'description': (
            'Your RFQ or message has reached the SONNE engineering and '
            'sales team. Here is what happens next and how to add '
            'technical details.'
        ),
    },
    'terms-of-service': {
        'title': 'Website Terms of Service | SONNE',
        'description': (
            'The terms that apply to using the SONNE website, the scope '
            'of published content, and how to contact us with a question.'
        ),
    },
    'privacy-policy': {
        'title': 'Privacy Policy | SONNE',
        'description': (
            'How SONNE handles information submitted through this website, '
            'including contact and RFQ forms, file uploads, cookies and '
            'requests to access or delete data.'
        ),
    },
    'sitemap': {
        'title': 'Website Sitemap | SONNE',
        'description': (
            'Every planned SONNE page grouped by products, solutions, '
            'engineering, resources and company sections.'
        ),
    },
}

ROUTES = {}
for slug, (page_id, url) in contract.TARGETS.items():
    ROUTES[slug] = {
        'path': url if url == '/' else url + '/',
        'h1': contract.FRAGMENT_PAGES[page_id]['h1'] if page_id in contract.FRAGMENT_PAGES else None,
        'wrapper': contract.WRAPPERS[slug],
        'tdk': contract.expected_tdk(page_id),
        'strict': True,
    }
ROUTES['request-a-quote'] = {
    'path': '/request-a-quote/',
    'h1': contract.RFQ_H1,
    'wrapper': contract.WRAPPERS['request-a-quote'],
    'tdk': contract.expected_tdk('page-31'),
    'strict': True,
}
for slug in ('thank-you', 'terms-of-service', 'privacy-policy', 'sitemap'):
    ROUTES[slug] = {
        'path': '/%s/' % slug,
        'h1': 'Privacy Policy' if slug == 'privacy-policy' else None,
        'wrapper': contract.WRAPPERS[slug],
        'tdk': SYSTEM_TDK[slug],
        'strict': True,
    }
for slug, path in (('resources', '/resources/'), ('insights', '/resources/insights/')):
    ROUTES[slug] = {
        'path': path,
        'h1': None,
        'wrapper': None,
        'tdk': None,
        'strict': False,
    }


def fetch(path):
    status, headers, body = bs.request(DOMAIN + path)
    return status, headers, body.decode('utf-8', 'replace')


def text_of(fragment):
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', fragment)).split())


def norm_h1(fragment):
    # WordPress wptexturize renders straight quotes as curly entities in the_content.
    return text_of(fragment).replace('\u2018', "'").replace('\u2019', "'")


def norm_path(path):
    return path if path == '/' else path.rstrip('/')


def main():
    bs.establish_bypass()
    docs = {}
    failures = []
    warnings = []
    print('== Route checks ==')
    for slug, spec_row in ROUTES.items():
        status, headers, body = fetch(spec_row['path'])
        docs[slug] = body
        problems = []
        if status != 200:
            problems.append('status %s' % status)
        title = re.search(r'<title>(.*?)</title>', body, re.S)
        title_text = html.unescape(title.group(1)).strip() if title else ''
        desc = re.search(r'<meta name="description" content="([^"]*)"', body)
        desc_text = html.unescape(desc.group(1)).strip() if desc else ''
        if spec_row['strict']:
            if title_text != spec_row['tdk']['title']:
                problems.append('title %r != %r' % (title_text, spec_row['tdk']['title']))
            if desc_text != spec_row['tdk']['description']:
                problems.append('description mismatch: %r' % desc_text[:120])
        else:
            if not title_text:
                problems.append('missing title')
        h1s = [text_of(x) for x in re.findall(r'<h1[^>]*>(.*?)</h1>', body, re.S)]
        if len(h1s) != 1:
            problems.append('h1 count %d' % len(h1s))
        elif spec_row['h1'] and norm_h1(h1s[0]) != norm_h1(spec_row['h1']):
            problems.append('h1 %r != %r' % (h1s[0], spec_row['h1']))
        if spec_row['wrapper'] and ('class="%s"' % spec_row['wrapper']) not in body:
            problems.append('missing wrapper %s' % spec_row['wrapper'])
        canon = re.findall(r'<link rel="canonical" href="([^"]+)"', body)
        if len(canon) != 1:
            problems.append('canonical count %d' % len(canon))
        elif canon[0].rstrip('/') != (DOMAIN + spec_row['path']).rstrip('/'):
            problems.append('canonical %s' % canon[0])
        ld = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', body, re.S)
        for block in ld:
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                problems.append('bad json-ld: %s' % exc)
        if not ld:
            problems.append('no json-ld')
        for legacy in ('julong', 'sunglasses', 'wxkntest', 'wa.me/8613450284642'):
            if legacy in body.lower():
                problems.append('legacy marker %s' % legacy)
        for literal in ('[contact-form-7', '__CONTACT_FORM_ID__'):
            if literal in body:
                problems.append('literal shortcode %s' % literal)
        if problems:
            failures.append((slug, spec_row['path'], problems))
        print('%-22s %s  h1=%s  ld=%d' % (slug, status, len(h1s), len(ld)))

    print('\n== Contact form ==')
    contact = docs['contact']
    contact_checks = {
        'form element': 'wpcf7' in contact and '<form' in contact,
        'name field': 'name="your-name"' in contact and 'id="contact-name"' in contact,
        'company field': 'name="your-company"' in contact and 'id="contact-company"' in contact,
        'email field': 'name="your-email"' in contact and 'id="contact-email"' in contact,
        'topic field': 'name="contact-topic"' in contact and 'id="contact-topic"' in contact,
        'summary field': 'name="requirement-summary"' in contact and 'id="contact-summary"' in contact,
        'submit button': 'Send Message' in contact,
    }
    for label, ok in contact_checks.items():
        print('%-16s %s' % (label, 'OK' if ok else 'FAIL'))
        if not ok:
            failures.append(('contact', '/contact/', [label]))

    print('\n== 404 template ==')
    status, headers, body = fetch('/this-page-should-not-exist-qa/')
    not_found_ok = status == 404 and 'Popular Destinations' in body and 'sn-404__hero' in body
    print('status', status, 'new template', not_found_ok)
    if not not_found_ok:
        failures.append(('404', '/this-page-should-not-exist-qa/', ['not the new 404 template']))

    print('\n== Internal links ==')
    route_paths = {norm_path(row['path']) for row in ROUTES.values()}
    internal = set()
    assets = set()
    for body in docs.values():
        for href in re.findall(r'href="([^"]+)"', body):
            if href.startswith(('mailto:', 'tel:', '#', 'javascript:')):
                continue
            parsed = urlsplit(urljoin(DOMAIN, href))
            if parsed.netloc and parsed.netloc != 'rf-sonne.com':
                continue
            path = parsed.path or '/'
            if path.startswith(('/wp-json', '/wp-admin', '/wp-login', '/feed')):
                continue
            if path in ('/xmlrpc.php', '/comments/feed', '/comments/feed/'):
                continue
            if path.startswith(('/wp-content', '/wp-includes')) or re.search(
                    r'\.(css|js|png|jpe?g|webp|svg|gif|ico|woff2?|ttf|xml|pdf)$', path, re.I):
                assets.add(path)
            else:
                internal.add(norm_path(path))
    unplanned = sorted(internal - route_paths)
    for path in unplanned:
        warnings.append('unplanned internal link %s' % path)
    print('routes from markup:', len(internal), 'assets:', len(assets))
    print('unplanned:', unplanned)

    print('\n== Internal link status ==')
    def check_link(path):
        status, _, body = bs.request(DOMAIN + path)
        return path, status, len(body)
    with ThreadPoolExecutor(max_workers=8) as pool:
        link_results = list(pool.map(check_link, sorted(internal)))
    broken_links = [(p, s) for p, s, _ in link_results if s != 200]
    print('links checked:', len(link_results), 'non-200:', len(broken_links))
    for p, s in broken_links:
        print('  BROKEN', s, p)
        failures.append(('link', p, ['status %s' % s]))

    print('\n== Assets and images ==')
    imgs = set()
    for body in docs.values():
        for tag in re.findall(r'<img\b[^>]*>', body):
            src = re.search(r'\bsrc="([^"]+)"', tag)
            if src:
                imgs.add(urlsplit(urljoin(DOMAIN, src.group(1))).path)
            srcset = re.search(r'\bsrcset="([^"]+)"', tag)
            if srcset:
                for part in srcset.group(1).split(','):
                    candidate = part.strip().split(' ')[0]
                    if candidate:
                        imgs.add(urlsplit(urljoin(DOMAIN, candidate)).path)
    asset_paths = sorted(assets | imgs)
    def check_asset(path):
        status, _, body = bs.request(DOMAIN + path)
        return path, status, len(body)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check_asset, asset_paths))
    bad = [(p, s) for p, s, _ in results if s not in (200, 206, 304)]
    print('assets checked:', len(results), 'broken:', len(bad))
    for p, s in bad[:20]:
        print('  BROKEN', s, p)
        failures.append(('asset', p, ['status %s' % s]))

    print('\n== Summary ==')
    print('failures:', len(failures))
    for row in failures[:30]:
        print(' ', row)
    print('warnings:', len(warnings))
    for row in warnings:
        print(' ', row)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / 'live-verification.json').write_text(json.dumps({
        'failures': failures,
        'warnings': warnings,
        'routes': list(ROUTES),
        'assets_checked': len(results),
        'links_checked': len(link_results),
        'images': sorted(imgs),
    }, indent=2), encoding='utf-8')
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
