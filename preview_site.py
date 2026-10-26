#!/usr/bin/env python3
"""Build and serve standalone local previews of the SONNE P3 fragments."""

from __future__ import annotations

import argparse
import ast
import html
import json
import mimetypes
import re
import shutil
import sys
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parent
WEBSITE = ROOT / 'website'
PREVIEW_DIR = ROOT / 'preview'
SONNE_CSS = ROOT / 'sonne.css'
MAIN_CSS = ROOT / 'main.css'
SITE_HEADER_JS = ROOT / 'assets' / 'site-header.js'
SOURCE_01 = ROOT / 'docs-strategy' / 'source-01.json'
DATA_DIR = ROOT / 'template-parts' / 'data'
RFQ_FORM_TEMPLATE = ROOT / 'cf7' / 'request-a-quote-form.html'
CONTACT_FORM_TEMPLATE = ROOT / 'cf7' / 'contact-form.html'
SITE_URL = 'https://rf-sonne.com'


@dataclass(frozen=True)
class PreviewPage:
    slug: str
    source_id: str
    route: str
    filename: str
    fragment: str


PREVIEW_PAGES = (
    PreviewPage('home', 'page-01', '/', 'index.html', 'home.html'),
    PreviewPage('products', 'page-02', '/products', 'products.html', 'products.html'),
    PreviewPage(
        'rf-microwave-filters',
        'page-03',
        '/products/rf-microwave-filters',
        'rf-microwave-filters.html',
        'rf-microwave-filters.html',
    ),
    PreviewPage(
        'waveguide-components',
        'page-04',
        '/products/waveguide-components',
        'waveguide-components.html',
        'waveguide-components.html',
    ),
    PreviewPage(
        'rf-combiners',
        'page-05',
        '/products/rf-combiners',
        'rf-combiners.html',
        'rf-combiners.html',
    ),
    PreviewPage(
        'base-station-rf',
        'page-06',
        '/products/base-station-rf',
        'base-station-rf.html',
        'base-station-rf.html',
    ),
    PreviewPage(
        'precision-enclosures',
        'page-07',
        '/products/precision-enclosures',
        'precision-enclosures.html',
        'precision-enclosures.html',
    ),
    PreviewPage(
        'ibs-das-components',
        'page-08',
        '/products/ibs-das-components',
        'ibs-das-components.html',
        'ibs-das-components.html',
    ),
    PreviewPage(
        'fttx-fiber-distribution',
        'page-09',
        '/products/fttx-fiber-distribution',
        'fttx-fiber-distribution.html',
        'fttx-fiber-distribution.html',
    ),
    PreviewPage(
        'rf-accessories',
        'page-10',
        '/products/rf-accessories',
        'rf-accessories.html',
        'rf-accessories.html',
    ),
    PreviewPage(
        'solutions', 'page-11', '/solutions', 'solutions.html', 'solutions.html'
    ),
    PreviewPage(
        '5g-base-station',
        'page-12',
        '/solutions/5g-base-station',
        '5g-base-station.html',
        '5g-base-station.html',
    ),
    PreviewPage(
        'microwave-backhaul',
        'page-13',
        '/solutions/microwave-backhaul',
        'microwave-backhaul.html',
        'microwave-backhaul.html',
    ),
    PreviewPage(
        'satellite-earth-station',
        'page-14',
        '/solutions/satellite-earth-station',
        'satellite-earth-station.html',
        'satellite-earth-station.html',
    ),
    PreviewPage(
        'das-ibs', 'page-15', '/solutions/das-ibs', 'das-ibs.html', 'das-ibs.html'
    ),
    PreviewPage('fttx', 'page-16', '/solutions/fttx', 'fttx.html', 'fttx.html'),
    PreviewPage(
        'data-center-enclosures',
        'page-17',
        '/solutions/data-center-enclosures',
        'data-center-enclosures.html',
        'data-center-enclosures.html',
    ),
    PreviewPage(
        'engineering',
        'page-18',
        '/engineering',
        'engineering.html',
        'engineering.html',
    ),
    PreviewPage(
        'custom-rf-design',
        'page-19',
        '/engineering/custom-rf-design',
        'custom-rf-design.html',
        'custom-rf-design.html',
    ),
    PreviewPage('npi', 'page-20', '/engineering/npi', 'npi.html', 'npi.html'),
    PreviewPage(
        'testing-quality',
        'page-21',
        '/engineering/testing-quality',
        'testing-quality.html',
        'testing-quality.html',
    ),
    PreviewPage(
        'manufacturing',
        'page-22',
        '/engineering/manufacturing',
        'manufacturing.html',
        'manufacturing.html',
    ),
    PreviewPage(
        'rfq-guide',
        'page-25',
        '/resources/rfq-guide',
        'rfq-guide.html',
        'rfq-guide.html',
    ),
    PreviewPage('faq', 'page-26', '/resources/faq', 'faq.html', 'faq.html'),
    PreviewPage(
        'datasheets',
        'page-27',
        '/resources/datasheets',
        'datasheets.html',
        'datasheets.html',
    ),
    PreviewPage('about', 'page-28', '/about', 'about.html', 'about.html'),
    PreviewPage('factory', 'page-29', '/about/factory', 'factory.html', 'factory.html'),
    PreviewPage('contact', 'page-30', '/contact', 'contact.html', 'contact.html'),
    PreviewPage(
        'request-a-quote',
        'page-31',
        '/request-a-quote',
        'request-a-quote.html',
        'request-a-quote.html',
    ),
    PreviewPage('thank-you', '', '/thank-you', 'thank-you.html', 'thank-you.html'),
    PreviewPage(
        'terms-of-service',
        '',
        '/terms-of-service',
        'terms-of-service.html',
        'terms-of-service.html',
    ),
    PreviewPage(
        'privacy-policy',
        '',
        '/privacy-policy',
        'privacy-policy.html',
        'privacy-policy.html',
    ),
    PreviewPage('sitemap', '', '/sitemap', 'sitemap.html', 'sitemap.html'),
)

SYSTEM_PREVIEW_TDK = {
    'thank-you': {
        'title': 'Thank You — Request Received | SONNE',
        'description': (
            'Your RFQ or message has reached the SONNE engineering and sales '
            'team. Here is what happens next and how to add technical details.'
        ),
    },
    'terms-of-service': {
        'title': 'Website Terms of Service | SONNE',
        'description': (
            'The terms that apply to using the SONNE website, the scope of '
            'published content, and how to contact us with a question.'
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


def page_tdk(page, tdk_by_id):
    return tdk_by_id.get(page.source_id) or SYSTEM_PREVIEW_TDK[page.slug]


def normalize_route(raw_path):
    path = unquote(urlsplit(raw_path).path or '/')
    return '/' if path == '/' else path.rstrip('/')


ROUTE_FILES = {page.route: page.filename for page in PREVIEW_PAGES}
ASSET_FILES = {
    '/assets/main.css': MAIN_CSS,
    '/assets/sonne.css': SONNE_CSS,
    '/assets/site-header.js': SITE_HEADER_JS,
}


def _future_routes():
    routes = set()
    if SOURCE_01.is_file():
        for page in json.loads(SOURCE_01.read_text(encoding='utf-8')):
            route = normalize_route(page.get('url', ''))
            if route and route not in ROUTE_FILES:
                routes.add(route)
    return frozenset(routes)


FUTURE_ROUTES = _future_routes()


def resolve_request(raw_path, preview_dir=PREVIEW_DIR):
    route = normalize_route(raw_path)
    filename = ROUTE_FILES.get(route)
    if filename is not None:
        candidate = Path(preview_dir) / filename
        return candidate if candidate.is_file() else None
    asset = ASSET_FILES.get(route)
    if asset is not None:
        return asset if asset.is_file() else None
    return None


def _strip_php(source):
    source = source.replace('<?php', '').replace('?>', '')
    output = []
    index = 0
    in_single = in_double = in_line = in_block = False
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ''
        if in_line:
            if character == '\n':
                in_line = False
                output.append(character)
            index += 1
            continue
        if in_block:
            if character == '*' and following == '/':
                in_block = False
                index += 2
                continue
            index += 1
            continue
        if in_single or in_double:
            output.append(character)
            if character == '\\' and following:
                output.append(following)
                index += 2
                continue
            if (in_single and character == "'") or (in_double and character == '"'):
                in_single = in_double = False
            index += 1
            continue
        if character == "'":
            in_single = True
        elif character == '"':
            in_double = True
        elif character == '/' and following == '/':
            in_line = True
            index += 2
            continue
        elif character == '/' and following == '*':
            in_block = True
            index += 2
            continue
        output.append(character)
        index += 1
    return ''.join(output)


def _balanced_array(source, start):
    if not source.startswith('array(', start):
        raise ValueError(f'expected array() at offset {start}')
    depth = 0
    for index in range(start + len('array(') - 1, len(source)):
        character = source[index]
        if character == '(':
            depth += 1
        elif character == ')':
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise ValueError('unterminated PHP array literal')


class _PhpArrayParser:
    def __init__(self, text, variables=None):
        self.text = text
        self.pos = 0
        self.variables = variables or {}

    def _error(self, message):
        raise ValueError(f'{message} at offset {self.pos}: {self.text[self.pos:self.pos + 40]!r}')

    def _skip_space(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def parse(self):
        value = self._value()
        self._skip_space()
        if self.pos != len(self.text):
            self._error('unexpected trailing characters')
        return value

    def _value(self):
        self._skip_space()
        if self.text.startswith('array', self.pos):
            boundary = self.pos + 5
            if boundary == len(self.text) or not (
                self.text[boundary].isalnum() or self.text[boundary] == '_'
            ):
                return self._array()
        if self.pos < len(self.text) and self.text[self.pos] == '$':
            variable = re.match(r'\$(\w+)', self.text[self.pos:])
            if variable is None:
                self._error('unsupported PHP variable')
            name = variable.group(1)
            if name not in self.variables:
                self._error(f'unknown PHP variable {name}')
            self.pos += variable.end()
            value = self.variables[name]
            self._skip_space()
            if self.pos < len(self.text) and self.text[self.pos] == '[':
                self.pos += 1
                key = self._string()
                self._skip_space()
                if self.pos >= len(self.text) or self.text[self.pos] != ']':
                    self._error('expected ] after PHP array key')
                self.pos += 1
                if key not in value:
                    self._error(f'unknown PHP array key {key!r}')
                value = value[key]
            return value
        if self.pos < len(self.text) and self.text[self.pos] in {'\'', '"'}:
            return self._string()
        number = re.match(r'-?\d+(?:\.\d+)?', self.text[self.pos:])
        if number:
            literal = number.group(0)
            self.pos += len(literal)
            return float(literal) if '.' in literal else int(literal)
        self._error('unsupported PHP value')

    def _string(self):
        quote_character = self.text[self.pos]
        start = self.pos
        self.pos += 1
        while self.pos < len(self.text):
            character = self.text[self.pos]
            self.pos += 1
            if character == '\\' and self.pos < len(self.text):
                self.pos += 1
            elif character == quote_character:
                return ast.literal_eval(self.text[start:self.pos])
        self._error('unterminated PHP string')

    def _array(self):
        self.pos += len('array')
        self._skip_space()
        if self.pos >= len(self.text) or self.text[self.pos] != '(':
            self._error('expected ( after array')
        self.pos += 1
        values = []
        associative = False
        while True:
            self._skip_space()
            if self.pos < len(self.text) and self.text[self.pos] == ')':
                self.pos += 1
                break
            first = self._value()
            self._skip_space()
            if self.text.startswith('=>', self.pos):
                associative = True
                self.pos += 2
                values.append((first, self._value()))
            else:
                values.append(first)
            self._skip_space()
            if self.pos < len(self.text) and self.text[self.pos] == ',':
                self.pos += 1
                continue
            if self.pos < len(self.text) and self.text[self.pos] == ')':
                self.pos += 1
                break
            self._error('expected , or ) in PHP array')
        if associative:
            return dict(values)
        return values


def _php_array_to_python(expression, variables=None):
    expression = re.sub(
        r"home_url\(\s*'([^']*)'\s*\)",
        lambda match: repr(match.group(1)),
        expression,
    )
    try:
        return _PhpArrayParser(expression, variables).parse()
    except (SyntaxError, ValueError) as error:
        raise ValueError(f'unsupported PHP array literal: {error}') from error


def _php_assignments(source):
    assignments = {}
    for match in re.finditer(r'\$(\w+)\s*=\s*array\s*\(', source):
        literal = _balanced_array(source, match.end() - len('array('))
        assignments[match.group(1)] = _php_array_to_python(literal)
    return assignments


def _php_return_value(source):
    source = _strip_php(source)
    assignments = _php_assignments(source)
    return_match = re.search(r'\breturn\b', source)
    if return_match is None:
        raise ValueError('PHP data file has no return statement')
    array_start = source.find('array', return_match.end())
    if array_start < 0:
        raise ValueError('PHP return statement does not return an array')
    literal = _balanced_array(source, array_start)
    return _php_array_to_python(literal, assignments)


def _load_php_data(filename):
    return _php_return_value((DATA_DIR / filename).read_text(encoding='utf-8'))


def load_chrome_data():
    return {
        'contact': _load_php_data('site-contact.php'),
        'header': _load_php_data('header-navigation.php'),
        'footer_groups': _load_php_data('footer-groups.php'),
    }


def _escape(value):
    return html.escape(str(value), quote=True)


def _render_desktop_nav(navigation, defaults):
    items = []
    for item in navigation:
        children = item.get('children') or []
        classes = 'site-nav__item has-children' if children else 'site-nav__item'
        caret = (
            '\n          <span class="site-nav__caret" aria-hidden="true"></span>'
            if children
            else ''
        )
        dropdown = ''
        if children and item.get('kind') == 'mega':
            columns = []
            for group in children:
                links = ''.join(
                    f'<li><a href="{_escape(link["url"])}" class="mega-item hover-trigger"'
                    f' data-img="{_escape(link.get("preview_image") or defaults["default_preview_image"])}"'
                    f' data-alt="{_escape(link["label"])}">{_escape(link["label"])}</a></li>'
                    for link in group.get('links') or []
                )
                columns.append(
                    '            <div class="site-nav__mega-column">'
                    f'<p class="site-nav__mega-title"><a href="{_escape(group["url"])}">'
                    f'{_escape(group["title"])}</a></p>'
                    f'<ul class="site-nav__dropdown-list">{links}</ul></div>'
                )
            dropdown = (
                '\n        <div class="site-nav__dropdown site-nav__dropdown--mega">'
                '<div class="site-nav__mega-inner"><div class="site-nav__mega-grid">'
                + ''.join(columns)
                + '</div><div class="site-nav__mega-preview">'
                f'<img src="{_escape(item.get("default_preview_image") or defaults["default_preview_image"])}"'
                ' id="productPreviewImg"'
                f' alt="{_escape(item.get("default_preview_alt") or defaults["default_preview_alt"])}"'
                ' width="1024" height="1024"></div></div>'
                '<div class="site-nav__mega-footer">'
                f'<p class="site-nav__mega-footnote">{_escape(item.get("footer_copy") or defaults["footer_copy"])}</p>'
                '<a href="/products/" class="btn-mega-action">Explore all products &rarr;</a>'
                '</div></div>'
            )
        elif children:
            links = ''.join(
                f'<li><a href="{_escape(child["url"])}">{_escape(child["label"])}</a></li>'
                for child in children
            )
            dropdown = (
                '\n        <div class="site-nav__dropdown">'
                f'<ul class="site-nav__dropdown-list">{links}</ul></div>'
            )
        items.append(
            f'\n      <li class="{classes}">'
            f'<a class="site-nav__link" href="{_escape(item["url"])}">'
            f'{_escape(item["label"])}{caret}</a>{dropdown}</li>'
        )
    return (
        '<nav class="site-nav site-nav--desktop" aria-label="Primary navigation">'
        '<ul class="site-nav__list">' + ''.join(items) + '</ul></nav>'
    )


def _render_mobile_nav(navigation):
    items = []
    for item in navigation:
        children = item.get('children') or []
        toggle = (
            '<button class="site-mobile-nav__toggle" type="button"'
            ' aria-expanded="false">More</button>'
            if children
            else ''
        )
        submenu = ''
        if children:
            if item.get('kind') == 'mega':
                groups = ''.join(
                    '<div class="site-mobile-nav__submenu-group">'
                    f'<p class="site-mobile-nav__submenu-title"><a href="{_escape(group["url"])}">'
                    f'{_escape(group["title"])}</a></p><ul>'
                    + ''.join(
                        f'<li><a href="{_escape(link["url"])}">{_escape(link["label"])}</a></li>'
                        for link in group.get('links') or []
                    )
                    + '</ul></div>'
                    for group in children
                )
            else:
                groups = '<ul>' + ''.join(
                    f'<li><a href="{_escape(child["url"])}">{_escape(child["label"])}</a></li>'
                    for child in children
                ) + '</ul>'
            submenu = f'<div class="site-mobile-nav__submenu" hidden>{groups}</div>'
        items.append(
            '<li class="site-mobile-nav__item"><div class="site-mobile-nav__row">'
            f'<a class="site-mobile-nav__link" href="{_escape(item["url"])}">'
            f'{_escape(item["label"])}</a>{toggle}</div>{submenu}</li>'
        )
    return ''.join(items)


def render_header(chrome):
    contact = chrome['contact']
    header_config = chrome['header']
    navigation = header_config['navigation']
    defaults = header_config['mega_menu_defaults']
    email = contact['email']
    phone = contact['phone']
    phone_href = contact['phone_href']
    quote_subject = quote(contact['quote_subject'], safe='')
    email_href = f'mailto:{email}?subject={quote_subject}'

    return f'''<div id="site-top" aria-hidden="true"></div>
<header class="site-header-shell">
  <div class="site-utility-bar">
    <div class="container-xl sn-container site-utility-bar__inner">
      <p class="site-utility-bar__message">Custom RF &amp; microwave components and precision enclosures.</p>
      <div class="site-utility-bar__links">
        <a href="tel:{_escape(phone_href)}">{_escape(phone)}</a>
        <a href="{_escape(email_href)}">{_escape(email)}</a>
        <a href="/contact/">Contact</a>
      </div>
    </div>
  </div>
  <div class="site-header">
    <div class="container-xl sn-container site-header__inner">
      <div class="site-branding">
        <a class="site-branding__link" href="/" aria-label="SONNE home">
          <img src="{_escape(contact['logo_url'])}" alt="{_escape(contact['logo_alt'])}"
            class="site-branding__logo" width="381" height="102"
            data-base-height="40px" data-scroll-height="34px">
        </a>
      </div>
      {_render_desktop_nav(navigation, defaults)}
      <div class="site-header__actions">
        <a class="sn-btn sn-btn--primary" href="/request-a-quote/">Request a Quote</a>
        <button class="site-menu-toggle" type="button" aria-expanded="false" aria-controls="site-mobile-nav">
          <span></span><span></span><span></span>
          <span class="screen-reader-text">Toggle navigation</span>
        </button>
      </div>
    </div>
  </div>
  <div class="site-mobile-nav" id="site-mobile-nav" hidden>
    <div class="site-mobile-nav__panel">
      <div class="site-mobile-nav__header">
        <div>
          <p class="site-mobile-nav__brand">{_escape(contact['brand_name'])}</p>
          <p class="site-mobile-nav__subline">Custom RF, microwave and enclosure engineering.</p>
        </div>
        <button class="site-mobile-nav__close" type="button" aria-label="Close navigation">Close</button>
      </div>
      <div class="site-mobile-nav__body">
        <ul class="site-mobile-nav__list">{_render_mobile_nav(navigation)}</ul>
        <div class="site-mobile-nav__contact">
          <a class="sn-btn sn-btn--primary" href="/request-a-quote/">Request a Quote</a>
          <a href="mailto:{_escape(email)}">{_escape(email)}</a>
          <a href="tel:{_escape(phone_href)}">{_escape(phone)}</a>
        </div>
      </div>
    </div>
  </div>
</header>'''


def render_footer(chrome):
    contact = chrome['contact']
    footer_groups = chrome['footer_groups']
    organization = {
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'Organization',
                '@id': f'{SITE_URL}/#organization',
                'name': contact['company_name'],
                'url': f'{SITE_URL}/',
                'email': contact['email'],
                'telephone': contact['phone'],
                'address': {
                    '@type': 'PostalAddress',
                    'streetAddress': contact['address_street'],
                    'addressLocality': contact['address_locality'],
                    'addressRegion': contact['address_region'],
                    'addressCountry': contact['address_country'],
                },
                'logo': {
                    '@type': 'ImageObject',
                    'url': contact['logo_url'],
                },
            },
            {
                '@type': 'WPFooter',
                'copyrightYear': 2026,
                'copyrightHolder': {'@id': f'{SITE_URL}/#organization'},
            },
        ],
    }
    menus = []
    for title, links in footer_groups.items():
        items = ''.join(
            f'<li><a href="{_escape(link["url"])}">{_escape(link["label"])}</a></li>'
            for link in links
        )
        menus.append(
            '<div class="site-footer__menu-group">'
            f'<p class="site-footer__menu-title">{_escape(title)}</p>'
            f'<ul class="site-footer__menu-list">{items}</ul></div>'
        )
    schema = json.dumps(organization, separators=(',', ':'), ensure_ascii=False)

    return f'''<footer class="site-footer">
  <script type="application/ld+json">{schema}</script>
  <div class="container-xl sn-container">
    <div class="site-footer__top">
      <div class="site-footer__brand">
        <a class="site-footer__brand-logo-link" href="/" aria-label="{_escape(contact['brand_name'])} home">
          <img src="{_escape(contact['logo_url'])}" alt="{_escape(contact['logo_alt'])}"
            class="site-footer__brand-logo" width="381" height="102">
        </a>
        <p class="site-footer__brand-copy">
          Custom RF and microwave components, waveguide assemblies and precision enclosures for engineering-led projects.
        </p>
        <div class="site-footer__brand-actions">
          <a class="sn-btn sn-btn--primary" href="/request-a-quote/">Request a Quote</a>
        </div>
      </div>
      <div class="site-footer__menus">
        {''.join(menus)}
        <div class="site-footer__menu-group">
          <p class="site-footer__menu-title">Contact</p>
          <ul class="site-footer__menu-list site-footer__contact-list">
            <li><a href="mailto:{_escape(contact['email'])}">{_escape(contact['email'])}</a></li>
            <li><a href="/contact/">Contact SONNE</a></li>
            <li><a href="/request-a-quote/">Request a Quote</a></li>
          </ul>
        </div>
      </div>
    </div>
    <div class="site-footer__contact-details">
      <a class="site-footer__contact-detail" href="tel:{_escape(contact['phone_href'])}">
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.58 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1 11.4 11.4 0 0 0 .58 3.6 1 1 0 0 1-.25 1z" fill="currentColor"/></svg>
        <span>
          <span class="site-footer__contact-label">Telephone</span>
          <span class="site-footer__contact-value">{_escape(contact['phone'])}</span>
        </span>
      </a>
      <div class="site-footer__contact-detail">
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z" fill="currentColor"/></svg>
        <span>
          <span class="site-footer__contact-label">Manufacturing base</span>
          <span class="site-footer__contact-value">{_escape(contact['address'])}</span>
        </span>
      </div>
    </div>
    <div class="site-footer__bottom">
      <p>&copy; 2026 {_escape(contact['company_name'])}. All rights reserved.</p>
      <div class="site-footer__bottom-links">
        <a href="/privacy-policy/">Privacy Policy</a>
        <a href="/terms-of-service/">Terms of Service</a>
        <a href="/sitemap/">Sitemap</a>
      </div>
      <a href="#site-top" class="site-footer__back-top" aria-label="Back to top" data-back-top>
        <span class="site-footer__back-top-label">Back to top</span>
        <span class="site-footer__back-top-icon" aria-hidden="true"></span>
      </a>
    </div>
  </div>
</footer>
<script>
document.addEventListener('DOMContentLoaded', function () {{
  var backTop = document.querySelector('[data-back-top]');
  if (!backTop) {{ return; }}

  var footer = document.querySelector('.site-footer');
  var footerVisible = false;

  function toggleBackTop() {{
    var shouldShow = window.scrollY > 400;
    if (footerVisible) {{ shouldShow = false; }}
    backTop.classList.toggle('is-visible', shouldShow);
  }}

  if (footer) {{
    if ('IntersectionObserver' in window) {{
      new IntersectionObserver(function (entries) {{
        footerVisible = entries[0].isIntersecting;
        toggleBackTop();
      }}, {{ threshold: 0 }}).observe(footer);
    }}
  }}

  window.addEventListener('scroll', toggleBackTop, {{ passive: true }});
  toggleBackTop();

  backTop.addEventListener('click', function (event) {{
    event.preventDefault();
    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({{ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' }});
  }});
}});
</script>'''


def load_tdk():
    pages = json.loads(SOURCE_01.read_text(encoding='utf-8'))
    result = {}
    for page in pages:
        lines = page['tdk'].splitlines()
        result[page['id']] = {
            'title': lines[lines.index('SEO Title') + 1].strip(),
            'description': lines[lines.index('Meta Description') + 1].strip(),
        }
    return result


CF7_TAG_RE = re.compile(r'\[([a-z][a-z0-9_-]*)(\*)?((?:\s+[^\]]*)?)\]', re.IGNORECASE)
CF7_PAIR_KEYS = {
    'placeholder',
    'id',
    'class',
    'autocomplete',
    'default',
    'limit',
    'filetypes',
    'min',
    'max',
    'step',
    'rows',
}


def _cf7_tokens(raw):
    tokens = []
    current = []
    quote = None
    for character in raw:
        if quote:
            if character == quote:
                tokens.append((''.join(current), True))
                current = []
                quote = None
            else:
                current.append(character)
        elif character in {'"', "'"}:
            quote = character
        elif character.isspace():
            if current:
                tokens.append((''.join(current), False))
                current = []
        else:
            current.append(character)
    if current:
        tokens.append((''.join(current), False))
    return tokens


def _parse_cf7_tag(match):
    basetype = match.group(1).lower()
    required = bool(match.group(2))
    tokens = _cf7_tokens(match.group(3).strip())
    if not tokens:
        return None
    if basetype == 'submit':
        return {
            'type': basetype,
            'required': required,
            'name': '',
            'options': {},
            'values': [text for text, quoted in tokens if quoted],
            'flags': set(),
        }
    name = tokens[0][0]
    options = {}
    values = []
    flags = set()
    index = 1
    while index < len(tokens):
        text, quoted = tokens[index]
        if quoted:
            values.append(text)
        elif ':' in text:
            key, value = text.split(':', 1)
            options[key] = value
        elif text in {'include_blank', 'use_label_element', 'multiple'}:
            flags.add(text)
        elif index + 1 < len(tokens) and tokens[index + 1][1] and text in CF7_PAIR_KEYS:
            options[text] = tokens[index + 1][0]
            index += 1
        else:
            flags.add(text)
        index += 1
    return {
        'type': basetype,
        'required': required,
        'name': name,
        'options': options,
        'values': values,
        'flags': flags,
    }


def _control_class(base, options):
    extra = options.get('class', '').strip()
    return f'{base} {extra}' if extra else base


def _input_attributes(tag, control_type):
    options = tag['options']
    name = tag['name']
    control_id = options.get('id') or name
    attributes = [
        f'type="{_escape(control_type)}"',
        f'id="{_escape(control_id)}"',
        f'name="{_escape(name)}"',
        f'class="{_escape(_control_class("sn-rfq__input", options))}"',
    ]
    if options.get('placeholder'):
        attributes.append(f'placeholder="{_escape(options["placeholder"])}"')
    if options.get('autocomplete'):
        attributes.append(f'autocomplete="{_escape(options["autocomplete"])}"')
    if tag['required']:
        attributes.append('required aria-required="true"')
    return ' '.join(attributes)


def _render_choice_group(tag):
    name = tag['name']
    control_type = tag['type']
    control_class = 'wpcf7-radio' if control_type == 'radio' else 'wpcf7-checkbox'
    choices = []
    last = len(tag['values']) - 1
    for index, value in enumerate(tag['values']):
        attributes = [
            f'type="{control_type}"',
            f'id="{_escape(name)}-{index + 1}"',
            f'name="{_escape(name)}"',
            f'value="{_escape(value)}"',
        ]
        if tag['required']:
            attributes.append('required')
        suffix = ''
        if index == 0:
            suffix += ' first'
        if index == last:
            suffix += ' last'
        choices.append(
            f'<span class="wpcf7-list-item{suffix}"><label>'
            f'<input {" ".join(attributes)}>'
            f'<span class="wpcf7-list-item-label">{_escape(value)}</span>'
            '</label></span>'
        )
    return (
        f'<span class="wpcf7-form-control-wrap" data-name="{_escape(name)}">'
        f'<span class="wpcf7-form-control {control_class}" aria-invalid="false">'
        + ''.join(choices)
        + '</span></span>'
    )


def _render_select(tag):
    options = tag['options']
    name = tag['name']
    control_id = options.get('id') or name
    attributes = [
        f'id="{_escape(control_id)}"',
        f'name="{_escape(name)}"',
        f'class="{_escape(_control_class("sn-rfq__input", options))}"',
    ]
    if tag['required']:
        attributes.append('required aria-required="true"')
    option_markup = []
    if 'include_blank' in tag['flags']:
        option_markup.append('<option value="">Please select</option>')
    for value in tag['values']:
        option_markup.append(
            f'<option value="{_escape(value)}">{_escape(value)}</option>'
        )
    return f'<select {" ".join(attributes)}>{"".join(option_markup)}</select>'


def _render_textarea(tag):
    options = tag['options']
    name = tag['name']
    control_id = options.get('id') or name
    attributes = [
        f'id="{_escape(control_id)}"',
        f'name="{_escape(name)}"',
        f'class="{_escape(_control_class("sn-rfq__textarea", options))}"',
        f'rows="{_escape(options.get("rows", "4"))}"',
    ]
    if options.get('placeholder'):
        attributes.append(f'placeholder="{_escape(options["placeholder"])}"')
    if tag['required']:
        attributes.append('required aria-required="true"')
    return f'<textarea {" ".join(attributes)}></textarea>'


def _render_file(tag):
    options = tag['options']
    name = tag['name']
    control_id = options.get('id') or name
    extensions = [
        '.' + item.strip()
        for item in options.get('filetypes', '').split('|')
        if item.strip()
    ]
    attributes = [
        'type="file"',
        f'id="{_escape(control_id)}"',
        f'name="{_escape(name)}"',
        f'class="{_escape(_control_class("sn-rfq__file", options))}"',
    ]
    if extensions:
        attributes.append(f'accept="{_escape(",".join(extensions))}"')
    if tag['required']:
        attributes.append('required aria-required="true"')
    return f'<input {" ".join(attributes)}>'


def _render_cf7_template(source):
    def replace(match):
        tag = _parse_cf7_tag(match)
        if tag is None:
            return match.group(0)
        control_type = tag['type']
        if control_type == 'submit':
            label = tag['values'][0] if tag['values'] else 'Submit'
            return f'<button type="submit">{_escape(label)}</button>'
        if control_type in {'text', 'email', 'tel'}:
            return f'<input {_input_attributes(tag, control_type)}>'
        if control_type == 'textarea':
            return _render_textarea(tag)
        if control_type == 'select':
            return _render_select(tag)
        if control_type in {'radio', 'checkbox'}:
            return _render_choice_group(tag)
        if control_type == 'file':
            return _render_file(tag)
        return match.group(0)

    return CF7_TAG_RE.sub(replace, source)


def _cf7_form_markup(title):
    if title.strip().lower() == 'contact sonne':
        template = CONTACT_FORM_TEMPLATE
        form_class = 'sn-contact__form-fields'
        marker = 'data-contact-preview="true"'
    else:
        template = RFQ_FORM_TEMPLATE
        form_class = 'sn-rfq__form'
        marker = 'data-rfq-preview="true"'
    if not template.is_file():
        raise FileNotFoundError(f'missing CF7 template: {template}')
    form_markup = _render_cf7_template(template.read_text(encoding='utf-8'))
    return f'<form class="{form_class}" {marker} novalidate>{form_markup}</form>'


def render_cf7_shortcode(fragment):
    def replace(match):
        title = re.search(r'title="([^"]*)"', match.group(0))
        return _cf7_form_markup(title.group(1) if title else '')

    return re.sub(r'\[contact-form-7\b[^\]]*\]', replace, fragment)


def render_document(page, fragment, chrome, tdk):
    title = _escape(tdk['title'])
    description = _escape(tdk['description'])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="data:,">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="/assets/main.css">
<link rel="stylesheet" href="/assets/sonne.css">
</head>
<body>
{render_header(chrome)}
<main id="main-content">
{fragment}
</main>
{render_footer(chrome)}
<script src="/assets/site-header.js" defer></script>
</body>
</html>
'''


def build_preview(output_dir=PREVIEW_DIR):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    assets_dir = output / 'assets'
    assets_dir.mkdir(parents=True, exist_ok=True)
    for source, name in (
        (MAIN_CSS, 'main.css'),
        (SONNE_CSS, 'sonne.css'),
        (SITE_HEADER_JS, 'site-header.js'),
    ):
        shutil.copyfile(source, assets_dir / name)

    chrome = load_chrome_data()
    tdk_by_id = load_tdk()
    documents = []
    for page in PREVIEW_PAGES:
        fragment_path = WEBSITE / page.fragment
        if not fragment_path.is_file():
            raise FileNotFoundError(f'missing fragment: {fragment_path}')
        fragment = fragment_path.read_text(encoding='utf-8')
        if '[contact-form-7' in fragment:
            fragment = render_cf7_shortcode(fragment)
        document = render_document(page, fragment, chrome, page_tdk(page, tdk_by_id))
        destination = output / page.filename
        destination.write_text(document, encoding='utf-8', newline='\n')
        documents.append(destination)
    return documents


class PreviewHandler(BaseHTTPRequestHandler):
    server_version = 'SonnePreview/1.0'

    def _send_bytes(self, body, status, content_type, head_only=False):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _send_preview(self, head_only=False):
        resolved = resolve_request(self.path)
        if resolved is None:
            self._send_not_found(head_only)
            return
        content_type = mimetypes.guess_type(resolved.name)[0] or 'application/octet-stream'
        if content_type.startswith('text/') or content_type in {
            'application/javascript',
            'application/json',
        }:
            content_type = f'{content_type}; charset=utf-8'
        self._send_bytes(resolved.read_bytes(), HTTPStatus.OK, content_type, head_only)

    def _send_not_found(self, head_only=False):
        route = normalize_route(self.path)
        if route in FUTURE_ROUTES:
            detail = (
                'This 01 route is served by a WordPress template, not a static '
                'local preview.'
            )
        else:
            detail = 'This preview route does not exist.'
        body = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Preview route not available</title>
</head>
<body>
<main>
<h1>Preview route not available</h1>
<p>{_escape(detail)}</p>
<p><a href="/">Return to the preview home page</a></p>
</main>
</body>
</html>
'''.encode('utf-8')
        self._send_bytes(
            body,
            HTTPStatus.NOT_FOUND,
            'text/html; charset=utf-8',
            head_only,
        )

    def do_GET(self):
        self._send_preview()

    def do_HEAD(self):
        self._send_preview(head_only=True)

    def log_message(self, format, *args):
        sys.stderr.write(f'[preview] {format % args}\n')


def serve(port, output_dir=PREVIEW_DIR):
    documents = build_preview(output_dir)
    server = ThreadingHTTPServer(('127.0.0.1', port), PreviewHandler)
    print(f'Serving {len(documents)} SONNE preview documents at http://127.0.0.1:{port}/')
    for page in PREVIEW_PAGES:
        print(f'  http://127.0.0.1:{port}{page.route}')
    print('Unlisted 01 routes return 404; template-driven routes stay outside this preview.', flush=True)
    try:
        with server:
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return documents


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true', help='build the preview documents')
    parser.add_argument('--serve', action='store_true', help='build and serve the previews')
    parser.add_argument('--port', type=int, default=8765, help='local port (default: 8765)')
    args = parser.parse_args(argv)

    if args.serve:
        serve(args.port)
        return 0

    documents = build_preview()
    print(f'Built {len(documents)} preview documents in {PREVIEW_DIR}')
    for document in documents:
        print(f'  {document}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
