#!/usr/bin/env python3
"""SONNE Insights setup and verification helper. Never prints secrets."""
import base64
import importlib.util
import json
import re
import secrets
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[2]
SECRETS = json.loads((ROOT / 'w.secrets.json').read_text(encoding='utf-8'))
DOMAIN = 'https://rf-sonne.com'
USER = 'jewels923'
AUTH = 'Basic ' + base64.b64encode(f"{USER}:{SECRETS['app_password']}".encode()).decode()
CTX = ssl.create_default_context(cafile=certifi.where())
JAR = CookieJar()
OPENER = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=CTX),
    urllib.request.HTTPCookieProcessor(JAR),
)
CONFIG = json.loads((ROOT / 'inc' / 'data' / 'insights.json').read_text(encoding='utf-8'))
ARTIFACTS = ROOT / 'bak' / '2026-10-25-blog'
LEGACY = ('julong', 'wxkntest', 'sunglasses', 'sports eyewear', 'wa.me/8613450284642')


def request(url, headers=None, method='GET', data=None):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with OPENER.open(req, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


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
    status, _, body = request(
        f'{DOMAIN}/wp-json/hostinger-tools-plugin/v1/get-settings',
        headers={'Authorization': AUTH},
    )
    if status != 200:
        raise RuntimeError('bypass settings HTTP %s' % status)
    code = find_key(json.loads(body), 'bypass_code')
    if not code:
        raise RuntimeError('bypass code not found')
    request(f'{DOMAIN}/?bypass_code={urllib.parse.quote(code)}')


def api(path, method='GET', payload=None):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    headers = {'Authorization': AUTH}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    status, _, body = request(DOMAIN + path, headers=headers, method=method, data=data)
    parsed = json.loads(body) if body else None
    if status >= 400:
        raise RuntimeError('%s %s -> %s %s' % (method, path, status, parsed))
    return parsed


def sync_w():
    spec = importlib.util.spec_from_file_location('sonne_w', ROOT / 'w.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_temp_php(filename, php, query=''):
    w = sync_w()
    w.sync_request({'action': 'write_file', 'path': './' + filename, 'content': php, 'backup': False})
    url = f'{DOMAIN}/wp-content/themes/generatepress-child/{filename}'
    if query:
        url += '?' + query
    status, _, body = request(url)
    if status != 200:
        raise RuntimeError('%s -> HTTP %s %s' % (filename, status, body[:300]))
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise RuntimeError('%s returned non-JSON: %s' % (filename, body[:300].decode('utf-8', 'replace')))
    check, _, _ = request(f'{DOMAIN}/wp-content/themes/generatepress-child/{filename}')
    if check != 404:
        w.sync_request({'action': 'remove_file', 'path': './' + filename})
        check, _, _ = request(f'{DOMAIN}/wp-content/themes/generatepress-child/{filename}')
        if check != 404:
            raise RuntimeError('%s still reachable after cleanup' % filename)
    return payload


def state():
    establish_bypass()
    pages = api('/wp-json/wp/v2/pages?per_page=100&_fields=id,slug,link,parent,status,title')
    cats = api('/wp-json/wp/v2/categories?per_page=100&_fields=id,name,slug,count,link,description')
    posts = api('/wp-json/wp/v2/posts?per_page=100&_fields=id,slug,link,status,categories')
    settings = api('/wp-json/wp/v2/settings')
    data = {
        'pages': pages,
        'categories': cats,
        'posts': posts,
        'settings': {k: settings.get(k) for k in (
            'show_on_front', 'page_on_front', 'page_for_posts', 'posts_per_page',
            'default_category', 'default_comment_status', 'default_ping_status')},
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / 'live-state-after.json'
    if not (ARTIFACTS / 'live-state-before.json').exists():
        out = ARTIFACTS / 'live-state-before.json'
    out.write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(json.dumps(data['settings'], indent=2))
    print('pages:', [(p['id'], p['slug'], 'parent=%s' % p.get('parent')) for p in sorted(pages, key=lambda x: x['id'])])
    print('categories:', [(c['id'], c['slug'], c['count']) for c in cats])
    print('posts:', [(p['id'], p['slug'], p['status']) for p in posts])
    print('saved:', out)


def find_page(slug):
    rows = api('/wp-json/wp/v2/pages?per_page=100&slug=' + urllib.parse.quote(slug) + '&_fields=id,slug,link,parent,content,status')
    return rows[0] if rows else None


def ensure_page(slug, title, parent=0, content='', status='publish'):
    page = find_page(slug)
    payload = {'title': title, 'parent': parent, 'content': content, 'status': status}
    if page:
        return api('/wp-json/wp/v2/pages/%d' % page['id'], 'POST', payload)
    payload['slug'] = slug
    return api('/wp-json/wp/v2/pages', 'POST', payload)


def find_category(slug):
    rows = api('/wp-json/wp/v2/categories?per_page=100&slug=' + urllib.parse.quote(slug) + '&_fields=id,slug,name,count,link,description')
    return rows[0] if rows else None


def ensure_category(topic):
    category = find_category(topic['slug'])
    payload = {'name': topic['name'], 'slug': topic['slug'], 'description': topic['description']}
    if category:
        return api('/wp-json/wp/v2/categories/%d' % category['id'], 'POST', payload)
    return api('/wp-json/wp/v2/categories', 'POST', payload)


def set_page_meta(page_id, meta):
    payload = {
        'meta': {
            'rank_math_title': meta['title'],
            'rank_math_description': meta['description'],
            'rank_math_focus_keyword': meta['focus_keyword'],
        },
    }
    return api('/wp-json/seo-bridge/v1/update/%d' % page_id, 'POST', payload)


def set_term_meta(term_id, topic):
    payload = {
        'meta': {
            'rank_math_title': topic['seo_title'],
            'rank_math_description': topic['seo_description'],
            'rank_math_focus_keyword': topic['focus_keyword'],
        },
    }
    return api('/wp-json/seo-bridge/v1/term/category/%d' % term_id, 'POST', payload)


def set_settings(values):
    return api('/wp-json/wp/v2/settings', 'POST', values)


def configure_permalinks():
    token = secrets.token_hex(16)
    php = """<?php
if (!isset($_GET['token']) || !hash_equals('%s', (string) $_GET['token'])) {
    http_response_code(403);
    echo json_encode(array('error' => 'forbidden'));
    exit;
}
require_once dirname(__DIR__, 3) . '/wp-load.php';
global $wp_rewrite;
$wp_rewrite->set_permalink_structure('resources/insights/%%postname%%/');
$wp_rewrite->set_category_base('resources/insights/topic');
// Rebuild permastructs from the freshly saved options; flush_rules alone keeps the stale base.
$wp_rewrite->init();
$wp_rewrite->flush_rules(true);
wp_cache_flush();

$deleted = 0;
$cache = WP_CONTENT_DIR . '/cache/seraphinite-accelerator';
if (is_dir($cache)) {
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($cache, FilesystemIterator::SKIP_DOTS),
        RecursiveIteratorIterator::LEAVES_ONLY
    );
    foreach ($iterator as $file) {
        if ($file->isFile() && '.dat' === substr($file->getFilename(), -4)) {
            @unlink($file->getPathname());
            $deleted++;
        }
    }
}
if (has_action('litespeed_purge_all')) {
    do_action('litespeed_purge_all');
}

$insights = get_page_by_path('resources/insights');
$term = get_term_by('slug', 'rfq-preparation', 'category');
echo json_encode(array(
    'permalink_structure' => get_option('permalink_structure'),
    'category_base' => get_option('category_base'),
    'insights_url' => $insights ? get_permalink($insights) : '',
    'category_url' => ($term && !is_wp_error($term)) ? get_category_link($term->term_id) : '',
    'cache_files_deleted' => $deleted,
));
register_shutdown_function('unlink', __FILE__);
""" % token
    payload = run_temp_php('sonne-blog-options.php', php, 'token=' + token)
    print(json.dumps(payload, indent=2))
    return payload


def purge():
    token = secrets.token_hex(16)
    php = """<?php
if (!isset($_GET['token']) || !hash_equals('%s', (string) $_GET['token'])) {
    http_response_code(403);
    echo json_encode(array('error' => 'forbidden'));
    exit;
}
require_once dirname(__DIR__, 3) . '/wp-load.php';
wp_cache_flush();
$deleted = 0;
$cache = WP_CONTENT_DIR . '/cache/seraphinite-accelerator';
if (is_dir($cache)) {
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($cache, FilesystemIterator::SKIP_DOTS),
        RecursiveIteratorIterator::LEAVES_ONLY
    );
    foreach ($iterator as $file) {
        if ($file->isFile() && '.dat' === substr($file->getFilename(), -4)) {
            @unlink($file->getPathname());
            $deleted++;
        }
    }
}
if (has_action('litespeed_purge_all')) {
    do_action('litespeed_purge_all');
}
echo json_encode(array('cache_files_deleted' => $deleted));
register_shutdown_function('unlink', __FILE__);
""" % token
    payload = run_temp_php('sonne-blog-purge.php', php, 'token=' + token)
    print(json.dumps(payload, indent=2))
    return payload


def setup():
    establish_bypass()
    resources_html = (ROOT / 'website' / 'resources.html').read_text(encoding='utf-8')
    resources = ensure_page('resources', 'Resources', 0, resources_html)
    insights = ensure_page('insights', 'Insights', resources['id'], '')
    print('resources page:', resources['id'], resources['link'])
    print('insights page:', insights['id'], insights['link'])

    ids = {'resources': resources['id'], 'insights': insights['id'], 'categories': {}}
    for topic in CONFIG['topics']:
        category = ensure_category(topic)
        set_term_meta(category['id'], topic)
        ids['categories'][topic['slug']] = category['id']
        print('category:', category['id'], category['slug'])

    default_category = ids['categories']['rfq-preparation']
    set_settings({
        'page_for_posts': insights['id'],
        'posts_per_page': 9,
        'default_category': default_category,
        'default_comment_status': 'closed',
        'default_ping_status': 'closed',
    })

    rows = api('/wp-json/wp/v2/posts?per_page=100&slug=hello-world&_fields=id,slug,status')
    for row in rows:
        api('/wp-json/wp/v2/posts/%d' % row['id'], 'DELETE')
        print('trashed post:', row['id'], row['slug'])

    blog = find_category('blog')
    if blog and blog['id'] != default_category:
        api('/wp-json/wp/v2/categories/%d' % blog['id'], 'POST', {
            'name': 'Uncategorized',
            'slug': 'uncategorized',
        })
        print('renamed category:', blog['id'], 'blog -> uncategorized')

    set_page_meta(resources['id'], CONFIG['hub'])
    set_page_meta(insights['id'], CONFIG['page'])

    artifacts = ROOT / 'bak' / '2026-10-25-blog'
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / 'ids.json').write_text(json.dumps(ids, indent=2), encoding='utf-8')
    print('saved ids:', artifacts / 'ids.json')
    configure_permalinks()
    verify_routing()


def extract_title(html):
    match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
    return re.sub(r'\s+', ' ', match.group(1)).strip() if match else ''


def verify_routing():
    establish_bypass()
    paths = [
        '/resources/',
        '/resources/insights/',
        '/resources/insights/topic/rfq-preparation/',
        '/resources/insights/topic/filter-selection/',
        '/resources/insights/topic/waveguide-eband/',
        '/resources/insights/topic/low-pim-combiners/',
        '/resources/insights/topic/test-reports/',
        '/resources/insights/topic/npi-manufacturing/',
    ]
    failed = []
    for path in paths:
        status, _, body = request(DOMAIN + path, headers={'Accept': 'text/html'})
        html = body.decode('utf-8', 'replace')
        error = 'Fatal error' in html or 'critical error' in html.lower()
        print('%s -> %s | %s%s' % (path, status, extract_title(html) or '(no title)', ' | ERROR' if error else ''))
        if status != 200 or error:
            failed.append(path)
    if failed:
        raise SystemExit('routing failures: ' + ', '.join(failed))


def verify_files():
    w = sync_w()
    files = [
        'inc/data/insights.json', 'inc/insights.php', 'assets/css/sonne-insights.css', 'sonne.css',
        'home.php', 'category.php', 'single-post.php', 'archive.php', 'author.php',
        'header.php', 'functions.php',
    ]
    failed = []
    for rel in files:
        remote = w.sync_request({'action': 'read_file', 'path': './' + rel})
        data = remote['data']
        content = data['content']
        if data.get('encoding') == 'base64':
            content = base64.b64decode(content).decode('utf-8')
        local = (ROOT / rel).read_text(encoding='utf-8')
        ok = content.replace('\r\n', '\n') == local.replace('\r\n', '\n')
        print(('OK   ' if ok else 'DIFF ') + rel)
        if not ok:
            failed.append(rel)
    if failed:
        raise SystemExit('remote mismatch: ' + ', '.join(failed))


def inspect(path):
    establish_bypass()
    status, _, body = request(DOMAIN + path, headers={'Accept': 'text/html'})
    html = body.decode('utf-8', 'replace')
    print('url:', path)
    print('status:', status)
    canonicals = re.findall(r'<link[^>]+rel=["\']canonical["\'][^>]*>', html, re.I)
    print('canonical count:', len(canonicals))
    for tag in canonicals:
        href = re.search(r'href=["\']([^"\']+)', tag)
        print('canonical:', href.group(1) if href else tag)
    print('title:', extract_title(html))
    desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)', html, re.I)
    if not desc:
        desc = re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', html, re.I)
    print('description:', desc.group(1) if desc else '(none)')
    types = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            types.append('(invalid JSON-LD)')
            continue
        for item in parsed if isinstance(parsed, list) else [parsed]:
            if isinstance(item, dict):
                value = item.get('@type')
                types.append(value if isinstance(value, str) else json.dumps(value))
    print('schema types:', types or '(none)')
    print('contains /blog/:', '/blog/' in html)
    low = html.lower()
    print('legacy markers:', [marker for marker in LEGACY if marker in low] or 'none')
    print('fatal error:', 'Fatal error' in html)


TEMP_CONTENT = """<p>This temporary page verifies the SONNE Insights article template. It is not a published guide and will be removed after the checks.</p>
<h2>Inputs to confirm before an RFQ</h2>
<p>A reviewable request starts with the band plan, the port definition and the mechanical envelope. The table below lists the fields used in this verification. Each field affects how the topology is evaluated, how the mechanical interface is defined and which evidence has to accompany the sample.</p>
<table>
  <thead><tr><th>Field</th><th>Example</th><th>Why it matters</th></tr></thead>
  <tbody>
    <tr><td>Frequency range</td><td>3.4&ndash;3.8 GHz</td><td>Defines the tuning range and filter topology.</td></tr>
    <tr><td>Insertion loss</td><td>Target value</td><td>Trade-off against rejection and size.</td></tr>
    <tr><td>Interface</td><td>Connector or flange</td><td>Sets the mechanical and test fixture.</td></tr>
  </tbody>
</table>
<h3>Measurement conditions</h3>
<p>Record the test setup, calibration, frequency range, acceptance limits and sample identity. A number without conditions cannot be compared with another supplier. The same applies to rejection, isolation and return loss: the value is only meaningful together with the frequency span, the reference plane and the fixture used to obtain it. When a drawing describes a connector or flange, the interface standard, the material and the surface treatment belong in the same record.</p>
<p>For a multi-port assembly, state which port combinations were measured and how the unused ports were terminated. For a combined transmit and receive path, state the power level used during the test and whether the result was obtained with a continuous wave or a modulated signal. These details let an engineer reproduce the setup and judge whether the reported value applies to the intended operating case.</p>
<h3>Documents to attach</h3>
<p>Attach the drawing or 3D model, the band plan and any interface standard that the project has to follow. If only part of the information is available, note which fields are still open. An engineer can then identify the missing inputs instead of guessing them, and the first review can focus on feasibility rather than on basic definitions.</p>
<blockquote><p>Write down the missing inputs before asking for a quotation.</p></blockquote>
<h2>What the first review can cover</h2>
<p>The first review can check whether the requested band, interface and envelope are compatible with a candidate topology. It can also list the evidence that would be needed for acceptance, such as a frequency response plot, isolation data or a dimensional report. It does not replace a full design study, and it does not turn an incomplete description into a confirmed specification. The reviewer needs the actual inputs before any conclusion can be made.</p>
<p>For a filter, the review may compare a cavity approach with a waveguide approach and explain the trade-offs in insertion loss, rejection, power handling and size. For a waveguide assembly, the review may focus on flange type, polarization, tolerance and surface requirements. For a combiner, the review may start from the band plan and the port definitions. In each case the output is a list of assumptions and open questions that the buyer can confirm.</p>
<h3>Questions worth preparing</h3>
<ul>
  <li>Which frequency range must be covered, including guard bands?</li>
  <li>Which interface standard applies, and is a mating part defined?</li>
  <li>Which environmental conditions affect materials or finishes?</li>
  <li>Which evidence is required for first article acceptance?</li>
  <li>Which items are fixed, and which can still be adjusted?</li>
</ul>
<p>Preparing these answers shortens the review because the engineer does not have to ask for them one by one. It also creates a record that can be reused when the project moves from prototype to pilot run, and later to a repeat order.</p>
<h2>Next step</h2>
<p>Confirm the band plan, attach the drawing or model and state the validation requirements. Use the <a href="/request-a-quote/">RFQ form</a> when the inputs are ready. If a field is unknown, say so explicitly; an open question is easier to handle than an assumption that is never stated.</p>
<p>This paragraph exists only to give the template enough body text for a realistic reading-time check. It contains no product claim, no delivery promise and no pricing information. The text will be deleted together with the post after the template, table wrapper, table of contents and schema checks are complete.</p>
"""


def temp_post():
    establish_bypass()
    category = find_category('rfq-preparation')
    if not category:
        raise SystemExit('rfq-preparation category missing; run setup first')
    existing = api('/wp-json/wp/v2/posts?per_page=100&slug=template-verification-rfq-inputs&_fields=id,slug,status,link')
    if existing:
        post = existing[0]
    else:
        post = api('/wp-json/wp/v2/posts', 'POST', {
            'title': 'Template Verification: RFQ Inputs',
            'slug': 'template-verification-rfq-inputs',
            'categories': [category['id']],
            'excerpt': 'Temporary post used to verify the SONNE Insights template. It will be deleted after verification.',
            'content': TEMP_CONTENT,
            'status': 'publish',
        })
    print('post:', post['id'], post.get('link'), post.get('status'))
    (ARTIFACTS / 'temp-post.json').write_text(json.dumps({
        'id': post['id'], 'slug': 'template-verification-rfq-inputs', 'link': post.get('link'),
    }, indent=2), encoding='utf-8')


def delete_post():
    establish_bypass()
    path = ARTIFACTS / 'temp-post.json'
    if not path.exists():
        raise SystemExit('temp-post.json missing')
    info = json.loads(path.read_text(encoding='utf-8'))
    result = api('/wp-json/wp/v2/posts/%d?force=true' % info['id'], 'DELETE')
    print('deleted:', info['id'], result.get('deleted'))
    status, _, _ = request(info['link'])
    print('post url status:', status)
    if status != 404:
        raise SystemExit('temporary post still reachable: %s' % status)


def fetch_preview():
    establish_bypass()
    targets = {
        'resources.html': '/resources/',
        'insights.html': '/resources/insights/',
        'category-rfq-preparation.html': '/resources/insights/topic/rfq-preparation/',
        'post-template-verification.html': '/resources/insights/template-verification-rfq-inputs/',
    }
    out_dir = ARTIFACTS / 'preview'
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, path in targets.items():
        status, _, body = request(DOMAIN + path, headers={'Accept': 'text/html'})
        html = body.decode('utf-8', 'replace')
        html = re.sub(r'<head([^>]*)>', r'<head\1><base href="https://rf-sonne.com/">', html, count=1, flags=re.I)
        (out_dir / name).write_text(html, encoding='utf-8')
        print(name, status, len(html))


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'state'
    if command == 'state':
        state()
    elif command == 'setup':
        setup()
    elif command == 'configure-permalinks':
        configure_permalinks()
    elif command == 'purge':
        purge()
    elif command == 'verify-routing':
        verify_routing()
    elif command == 'verify-files':
        verify_files()
    elif command == 'inspect':
        if len(sys.argv) < 3:
            raise SystemExit('usage: blog_setup.py inspect <path>')
        inspect(sys.argv[2])
    elif command == 'temp-post':
        temp_post()
    elif command == 'delete-post':
        delete_post()
    elif command == 'fetch-preview':
        fetch_preview()
    else:
        raise SystemExit('unknown command: ' + command)


if __name__ == '__main__':
    main()
