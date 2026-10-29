#!/usr/bin/env python3
"""SONNE remaining P3 pages: snapshot, create, TDK, verify. Never prints secrets."""
import base64
import importlib.util
import json
import secrets
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / 'bak' / '2026-10-25-p3-full'
SOURCE = json.loads((ROOT / 'docs-strategy' / 'source-01.json').read_text(encoding='utf-8'))


def load_blog_setup():
    path = ROOT / 'bak' / 'qa' / 'blog_setup.py'
    spec = importlib.util.spec_from_file_location('sonne_blog_setup', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bs = load_blog_setup()

PAGES = [
    # slug, title, parent_slug, source url
    ('solutions', 'Solutions', '', '/solutions'),
    ('about', 'About SONNE', '', '/about'),
    ('ibs-das-components', 'IBS & DAS Components', 'products', '/products/ibs-das-components'),
    ('fttx-fiber-distribution', 'FTTX Fiber Distribution', 'products', '/products/fttx-fiber-distribution'),
    ('rf-accessories', 'RF Accessories', 'products', '/products/rf-accessories'),
    ('5g-base-station', '5G Base Station & RRU', 'solutions', '/solutions/5g-base-station'),
    ('microwave-backhaul', 'Microwave Backhaul', 'solutions', '/solutions/microwave-backhaul'),
    ('satellite-earth-station', 'Satellite & Earth Station', 'solutions', '/solutions/satellite-earth-station'),
    ('das-ibs', 'DAS & IBS', 'solutions', '/solutions/das-ibs'),
    ('fttx', 'FTTX Fiber to the Home', 'solutions', '/solutions/fttx'),
    ('data-center-enclosures', 'Data Center & Industrial Enclosures', 'solutions', '/solutions/data-center-enclosures'),
    ('custom-rf-design', 'Custom RF Design', 'engineering', '/engineering/custom-rf-design'),
    ('npi', 'From Prototype to Production (NPI)', 'engineering', '/engineering/npi'),
    ('testing-quality', 'Testing & Quality', 'engineering', '/engineering/testing-quality'),
    ('manufacturing', 'Precision Manufacturing', 'engineering', '/engineering/manufacturing'),
    ('rfq-guide', 'RFQ Guide & Checklist', 'resources', '/resources/rfq-guide'),
    ('faq', 'FAQ', 'resources', '/resources/faq'),
    ('datasheets', 'Datasheets & Drawings', 'resources', '/resources/datasheets'),
    ('factory', 'Factory & Equipment', 'about', '/about/factory'),
    ('contact', 'Contact', '', '/contact'),
    ('thank-you', 'Thank You', '', '/thank-you'),
    ('terms-of-service', 'Terms of Service', '', '/terms-of-service'),
    ('sitemap', 'Sitemap', '', '/sitemap'),
]

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
    'sitemap': {
        'title': 'Website Sitemap | SONNE',
        'description': (
            'Every planned SONNE page grouped by products, solutions, '
            'engineering, resources and company sections.'
        ),
    },
}


def tdk_for(url, slug):
    if slug in SYSTEM_TDK:
        tdk = dict(SYSTEM_TDK[slug])
        tdk['focus_keyword'] = ''
        return tdk
    page = next(p for p in SOURCE if p['url'] == url)
    lines = page['tdk'].splitlines()
    focus = ''
    kw = page.get('keywords', '').splitlines()
    if kw and kw[0].strip() == 'Focus' and len(kw) > 1:
        focus = kw[1].strip()
    return {
        'title': lines[lines.index('SEO Title') + 1].strip(),
        'description': lines[lines.index('Meta Description') + 1].strip(),
        'focus_keyword': focus,
    }


def snapshot():
    bs.establish_bypass()
    pages = bs.api('/wp-json/wp/v2/pages?per_page=100&context=edit'
                   '&_fields=id,slug,link,parent,status,title,content,template')
    settings = bs.api('/wp-json/wp/v2/settings')
    forms = bs.api('/wp-json/contact-form-7/v1/contact-forms')
    w = bs.sync_w()
    remote_404 = w.sync_request({'action': 'read_file', 'path': './404.php'})
    data = remote_404.get('data', {})
    raw = data.get('content', '')
    if data.get('encoding') == 'base64':
        raw = base64.b64decode(raw).decode('utf-8', 'replace')
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / 'live-before.json').write_text(json.dumps({
        'pages': pages,
        'settings': {k: settings.get(k) for k in (
            'show_on_front', 'page_on_front', 'page_for_posts', 'posts_per_page',
            'permalink_structure', 'default_comment_status', 'default_ping_status')},
        'cf7_forms': forms,
    }, indent=2, ensure_ascii=False), encoding='utf-8')
    (ARTIFACTS / '404.php.live-before').write_text(raw, encoding='utf-8')
    print('snapshot pages:', len(pages))
    for p in sorted(pages, key=lambda x: x['id']):
        print(' ', p['id'], p['slug'], 'parent=%s' % p.get('parent'), p['status'])
    print('settings:', json.dumps({k: settings.get(k) for k in (
        'show_on_front', 'page_on_front', 'page_for_posts', 'posts_per_page',
        'permalink_structure')}, ensure_ascii=False))
    print('cf7 forms:', [(f.get('id'), f.get('title', {}).get('rendered') or f.get('title')) for f in forms])


def create():
    bs.establish_bypass()
    ids = {}
    existing = bs.api('/wp-json/wp/v2/pages?per_page=100&_fields=id,slug,parent,status,link')
    by_slug = {p['slug']: p for p in existing}
    for slug, title, parent_slug, url in PAGES:
        parent_id = ids.get(parent_slug, 0)
        if parent_slug and parent_slug not in ids:
            parent = by_slug.get(parent_slug)
            if not parent:
                raise RuntimeError('missing parent page: %s' % parent_slug)
            parent_id = parent['id']
        page = by_slug.get(slug)
        if page:
            current = bs.api('/wp-json/wp/v2/pages/%d?context=edit&_fields=id,slug,parent,status' % page['id'])
            if current.get('parent') != parent_id:
                bs.api('/wp-json/wp/v2/pages/%d' % page['id'], 'POST', {'parent': parent_id})
                print('reparent', slug, '->', parent_id)
            ids[slug] = page['id']
            print('exists', slug, ids[slug])
            continue
        payload = {'slug': slug, 'title': title, 'parent': parent_id, 'status': 'publish', 'content': ''}
        result = bs.api('/wp-json/wp/v2/pages', 'POST', payload)
        ids[slug] = result['id']
        print('created', slug, result['id'], 'parent=%s' % parent_id)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / 'ids.json').write_text(json.dumps(ids, indent=2), encoding='utf-8')


def apply_tdk():
    bs.establish_bypass()
    ids = json.loads((ARTIFACTS / 'ids.json').read_text(encoding='utf-8'))
    for slug, _title, _parent, url in PAGES:
        tdk = tdk_for(url, slug)
        if not tdk['focus_keyword']:
            tdk['focus_keyword'] = tdk['title'].split('|')[0].strip()
        bs.set_page_meta(ids[slug], tdk)
        back = bs.api('/wp-json/seo-bridge/v1/read/%d' % ids[slug])
        meta = back.get('seo_meta', back)
        got = meta.get('rank_math_title')
        if got != tdk['title']:
            raise RuntimeError('TDK mismatch for %s: %r' % (slug, got))
        print('tdk ok', slug, '|', tdk['title'])


def verify_pages():
    bs.establish_bypass()
    pages = bs.api('/wp-json/wp/v2/pages?per_page=100&_fields=id,slug,link,parent,status,title')
    by_slug = {p['slug']: p for p in pages}
    missing = [s for s, *_ in PAGES if s not in by_slug]
    if missing:
        raise RuntimeError('missing pages: %s' % missing)
    for slug, title, parent_slug, url in PAGES:
        p = by_slug[slug]
        expected_link = 'https://rf-sonne.com' + (url + '/' if url != '/' else '/')
        parent_expected = by_slug[parent_slug]['id'] if parent_slug else 0
        print(slug, p['id'], p['link'], 'parent=%s/%s' % (p.get('parent'), parent_expected))
        if p['link'].rstrip('/') != expected_link.rstrip('/'):
            raise RuntimeError('link mismatch %s: %s vs %s' % (slug, p['link'], expected_link))
        if p.get('parent') != parent_expected:
            raise RuntimeError('parent mismatch %s: %s vs %s' % (slug, p.get('parent'), parent_expected))
    print('all %d pages verified' % len(PAGES))


def diagnose_contact_form(form_id=225):
    bs.establish_bypass()
    token = secrets.token_hex(16)
    php = """<?php
if (!isset($_GET['token']) || !hash_equals('%s', (string) $_GET['token'])) {
    http_response_code(403);
    echo json_encode(array('error' => 'forbidden'));
    exit;
}
register_shutdown_function(function () { @unlink(__FILE__); });
require_once dirname(__DIR__, 3) . '/wp-load.php';
$id = %d;
$form = wpcf7_contact_form($id);
if (!$form) { echo json_encode(array('error' => 'form not found')); exit; }
$out = array(
    'hash' => $form->hash(),
    'shortcode' => $form->shortcode(),
    'meta_form_len' => strlen((string) get_post_meta($id, '_form', true)),
    'meta_mail' => get_post_meta($id, '_mail', true),
    'meta_mail2' => get_post_meta($id, '_mail_2', true),
    'meta_messages_keys' => array_keys((array) get_post_meta($id, '_messages', true)),
    'meta_additional' => get_post_meta($id, '_additional_settings', true),
    'props_keys' => array_keys($form->get_properties()),
);
try {
    $out['html_len'] = strlen($form->form_html());
} catch (Throwable $e) {
    $out['html_error'] = get_class($e) . ': ' . $e->getMessage();
}
echo json_encode($out);
""" % (token, form_id)
    result = bs.run_temp_php('sonne-contact-check.php', php, 'token=' + urllib.parse.quote(token))
    print(json.dumps(result, ensure_ascii=False, indent=1))


def fix_contact_settings(form_id=225):
    bs.establish_bypass()
    form_html = (ROOT / 'cf7' / 'contact-form.html').read_text(encoding='utf-8')
    payload = base64.b64encode(form_html.encode('utf-8')).decode('ascii')
    token = secrets.token_hex(16)
    php = """<?php
if (!isset($_GET['token']) || !hash_equals('%s', (string) $_GET['token'])) {
    http_response_code(403);
    echo json_encode(array('error' => 'forbidden'));
    exit;
}
register_shutdown_function(function () { @unlink(__FILE__); });
require_once dirname(__DIR__, 3) . '/wp-load.php';
$id = %d;
$form = wpcf7_contact_form($id);
if (!$form) { echo json_encode(array('error' => 'form not found')); exit; }
$html = base64_decode((string) $_GET['form']);
$form->set_properties(array(
    'form' => $html,
    'additional_settings' => '',
));
$saved = $form->save();
$out = array(
    'saved' => $saved,
    'hash' => $form->hash(),
    'shortcode' => $form->shortcode(),
    'meta_form_type' => gettype(get_post_meta($id, '_form', true)),
    'meta_form_len' => strlen((string) get_post_meta($id, '_form', true)),
    'meta_additional_type' => gettype(get_post_meta($id, '_additional_settings', true)),
    'meta_additional' => get_post_meta($id, '_additional_settings', true),
);
try {
    $out['html_len'] = strlen($form->form_html());
} catch (Throwable $e) {
    $out['html_error'] = get_class($e) . ': ' . $e->getMessage();
}
echo json_encode($out);
""" % (token, form_id)
    query = 'token=%s&form=%s' % (urllib.parse.quote(token), urllib.parse.quote(payload))
    result = bs.run_temp_php('sonne-contact-fix.php', php, query)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    saved = bs.api('/wp-json/contact-form-7/v1/contact-forms/%d' % form_id)
    print('REST detail OK')
    print('mail recipient:', saved['properties']['mail']['recipient'])
    print('mail_2 recipient:', saved['properties']['mail_2']['recipient'])
    print('form ids:', all(x in saved['properties']['form']['content'] for x in (
        'contact-name', 'contact-company', 'contact-email', 'contact-topic', 'contact-summary')))


def cf7_forms():
    bs.establish_bypass()
    forms = bs.api('/wp-json/contact-form-7/v1/contact-forms')
    print(json.dumps(forms, indent=2, ensure_ascii=False))


def contact_properties():
    form_html = (ROOT / 'cf7' / 'contact-form.html').read_text(encoding='utf-8')
    mail_body = (
        '<h2>New contact message</h2>'
        '<p>A message was submitted through the SONNE contact page. '
        'Reply directly to the sender using Reply-To.</p>'
        '<p>Name: [your-name]<br>'
        'Company: [your-company]<br>'
        'Work email: [your-email]<br>'
        'Contact topic: [contact-topic]</p>'
        '<p>Requirement summary:<br>[requirement-summary]</p>'
    )
    messages = {
        'mail_sent_ok': (
            'Thank you. Your message has been sent to the SONNE team. '
            'A reply will come from info@zhide-tec.com.'
        ),
        'mail_sent_ng': (
            'The message could not be sent. Please try again, or email '
            'info@zhide-tec.com directly.'
        ),
        'validation_error': (
            'Some fields need attention. Please review the highlighted '
            'fields and submit again.'
        ),
        'spam': (
            'The submission was flagged as spam. Please try again, or email '
            'info@zhide-tec.com.'
        ),
        'invalid_required': 'Please complete this required field.',
        'invalid_too_long': 'This field is too long.',
        'invalid_too_short': 'This field is too short.',
        'invalid_email': 'Please enter a valid work email address.',
        'invalid_date': 'Please enter the date as YYYY-MM-DD.',
        'invalid_url': 'Please enter a valid URL.',
        'invalid_tel': 'Please enter a valid telephone number.',
        'invalid_number': 'Please enter a number.',
    }
    return {
        'form': {'content': form_html},
        'mail': {
            'active': True,
            'subject': 'Contact · [contact-topic] · [your-company]',
            'sender': 'SONNE Contact <wordpress@rf-sonne.com>',
            'recipient': 'info@zhide-tec.com',
            'body': mail_body,
            'additional_headers': 'Reply-To: [your-email]',
            'attachments': '',
            'use_html': True,
            'exclude_blank': True,
        },
        'mail_2': {
            'active': True,
            'subject': 'Contact copy · [contact-topic] · [your-company]',
            'sender': 'SONNE Contact <wordpress@rf-sonne.com>',
            'recipient': 'jason@riwick.com',
            'body': (
                '<h2>Contact copy</h2>'
                '<p>Name: [your-name]<br>Company: [your-company]<br>'
                'Work email: [your-email]<br>Topic: [contact-topic]</p>'
                '<p>Full details were sent to the SONNE inbox.</p>'
            ),
            'additional_headers': 'Reply-To: [your-email]',
            'attachments': '',
            'use_html': True,
            'exclude_blank': True,
        },
        'messages': messages,
        'additional_settings': {'content': ''},
    }


def create_contact_form():
    bs.establish_bypass()
    forms = bs.api('/wp-json/contact-form-7/v1/contact-forms')
    for f in forms:
        if f.get('title') == 'Contact SONNE':
            print('contact form already exists', f['id'], f.get('hash'))
            return
    props = contact_properties()
    payload = base64.b64encode(json.dumps(props).encode('utf-8')).decode('ascii')
    token = secrets.token_hex(16)
    php = """<?php
if (!isset($_GET['token']) || !hash_equals('%s', (string) $_GET['token'])) {
    http_response_code(403);
    echo json_encode(array('error' => 'forbidden'));
    exit;
}
register_shutdown_function(function () { @unlink(__FILE__); });
require_once dirname(__DIR__, 3) . '/wp-load.php';
if (!class_exists('WPCF7_ContactForm')) {
    echo json_encode(array('error' => 'cf7 missing'));
    exit;
}
$props = json_decode(base64_decode((string) $_GET['props']), true);
if (!is_array($props)) {
    echo json_encode(array('error' => 'bad props'));
    exit;
}
$form = WPCF7_ContactForm::get_template(array('title' => 'Contact SONNE', 'locale' => 'en_US'));
$form->set_properties($props);
$form->set_title('Contact SONNE');
$saved = $form->save();
echo json_encode(array(
    'id' => $form->id(),
    'title' => $form->title(),
    'hash' => $form->hash(),
    'shortcode' => $form->shortcode(),
    'saved' => $saved,
));
""" % token
    query = 'token=%s&props=%s' % (urllib.parse.quote(token), urllib.parse.quote(payload))
    result = bs.run_temp_php('sonne-contact-form.php', php, query)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / 'contact-form.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    if not result.get('id'):
        raise RuntimeError('contact form creation failed')
    saved = bs.api('/wp-json/contact-form-7/v1/contact-forms/%d' % result['id'])
    content = saved['properties']['form']['content']
    checks = ['contact-name', 'contact-company', 'contact-email', 'contact-topic', 'contact-summary']
    missing = [c for c in checks if c not in content]
    if missing:
        raise RuntimeError('saved form missing ids: %s' % missing)
    print('saved form verified:', result['shortcode'])


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'snapshot':
        snapshot()
    elif mode == 'create':
        create()
    elif mode == 'tdk':
        apply_tdk()
    elif mode == 'verify':
        verify_pages()
    elif mode == 'cf7':
        cf7_forms()
    elif mode == 'contact-form':
        create_contact_form()
    elif mode == 'diagnose-contact':
        diagnose_contact_form(int(sys.argv[2]) if len(sys.argv) > 2 else 225)
    elif mode == 'fix-contact':
        fix_contact_settings(int(sys.argv[2]) if len(sys.argv) > 2 else 225)
    else:
        raise SystemExit('unknown mode: ' + mode)
