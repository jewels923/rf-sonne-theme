import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / 'website'
UPLOAD_LOG = ROOT / 'images-upload-log.json'
PAGES_JSON = ROOT / 'pages.json'
NAV = ROOT / 'template-parts' / 'data' / 'header-navigation.php'
FOOTER = ROOT / 'template-parts' / 'data' / 'footer-groups.php'

PAGES = {
    'antenna-test-systems': 'Antenna and RF Test Systems for Production Lines',
    'switch-matrices': 'Solid-State Switch Matrices for RF Test and Signal Routing',
    'tr-modules': 'Ku, K and Ka-Band T/R Modules for Phased Arrays',
    'passive-microwave-components': 'High-Power Passive Microwave Components, DC–40 GHz',
    'rf-front-ends': 'Ku-Band Multi-Channel RF Front-Ends, 6–18 GHz',
}
WRAPPERS = {
    'antenna-test-systems': 'sn-test',
    'switch-matrices': 'sn-sw',
    'tr-modules': 'sn-trm',
    'passive-microwave-components': 'sn-pmc',
    'rf-front-ends': 'sn-rfe',
}
CHINESE = re.compile(r'[\u4e00-\u9fff]')
FORBIDDEN = (
    re.compile(r'\b\d+[- ](?:year|month)s?\s+warranty\b', re.I),
    re.compile(r'\b(?:MOQ|minimum order(?: quantity)?)\s*(?:of|is|:)?\s*\d+', re.I),
    re.compile(r'\bpayment terms?\s*(?:of|is|:)?\s*\d+', re.I),
    re.compile(r'\b(?:certified|guaranteed)\s+(?:for|to|by)\b', re.I),
    re.compile(r'\bguaranteed\b[^.]{0,80}\bfor\s+every\b', re.I),
    re.compile(r'\b(?:ISO|RoHS|REACH|IP\d{2})\b[^.]{0,40}\b(?:certified|guaranteed)\b', re.I),
)
TAGS = ('div', 'section', 'table', 'figure', 'details', 'ol', 'ul', 'thead', 'tbody', 'tr', 'th', 'td')


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


UPLOADS = load_json(UPLOAD_LOG)
MEDIA_URLS = {item['url'] for item in UPLOADS.values() if isinstance(item, dict) and item.get('url')}
WP_ROUTES = set()
for page in load_json(PAGES_JSON):
    route = urlsplit(page['url']).path or '/'
    WP_ROUTES.add(route if route == '/' else route.rstrip('/'))
for slug in PAGES:
    WP_ROUTES.add(f'/products/{slug}')
for post in (ROOT / 'content' / 'insights').glob('*.html'):
    WP_ROUTES.add(f'/resources/insights/{post.stem}')


def read(slug):
    return (WEBSITE / f'{slug}.html').read_text(encoding='utf-8')


class NewProductLineTest(unittest.TestCase):
    def test_page_basics(self):
        for slug, h1 in PAGES.items():
            with self.subTest(page=slug):
                source = read(slug)
                self.assertTrue(source.startswith('<!-- wp:html -->'))
                self.assertTrue(source.rstrip().endswith('<!-- /wp:html -->'))
                self.assertIn(f'<div class="{WRAPPERS[slug]}">', source)
                self.assertEqual(source.count('<h1'), 1)
                self.assertIn(f'<h1 id=', source)
                self.assertIn(h1, source)
                self.assertIn('class="sn-breadcrumbs"', source)
                self.assertIn('sn-hero-plate', source)
                self.assertIn('sn-hero-meta', source)
                self.assertIn('href="/request-a-quote/"', source)
                self.assertIn('sn-sheet', source)
                self.assertIsNone(CHINESE.search(source), 'Chinese characters in English page')
                self.assertNotIn('&&', source, 'bare && is corrupted by the WP HTML block')
                for tag in TAGS:
                    opening = len(re.findall(rf'<{tag}[\s>]', source))
                    closing = len(re.findall(rf'</{tag}>', source))
                    self.assertEqual(opening, closing, f'unbalanced <{tag}>')

    def test_figcaption_overlay_rule(self):
        for slug in PAGES:
            with self.subTest(page=slug):
                source = read(slug)
                self.assertRegex(
                    source,
                    r'figcaption \{ position: absolute; right: 0; bottom: 0; left: 0;',
                )
                self.assertRegex(source, r'figure \{ position: relative;')

    def test_ledger_cells_have_data_labels(self):
        for slug in PAGES:
            with self.subTest(page=slug):
                source = read(slug)
                for table in re.findall(r'<table\b.*?</table>', source, re.S):
                    body = table.split('<tbody>', 1)[-1]
                    for cell in re.findall(r'<td\b[^>]*>', body):
                        self.assertIn('data-label="', cell, f'<td> without data-label in {slug}')

    def test_json_ld_entities(self):
        for slug in PAGES:
            with self.subTest(page=slug):
                blocks = re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>',
                    read(slug),
                    re.S,
                )
                self.assertEqual(len(blocks), 1)
                graph = json.loads(blocks[0])['@graph']
                types = [node['@type'] for node in graph]
                self.assertEqual(types, ['Product', 'BreadcrumbList'])
                product, breadcrumb = graph
                self.assertEqual(product['url'], f'https://rf-sonne.com/products/{slug}/')
                self.assertEqual(product['@id'], f'https://rf-sonne.com/products/{slug}/#product')
                self.assertEqual(product['brand'], 'SONNE ELECTRONICS')
                self.assertIn(product['image'], MEDIA_URLS)
                crumbs = breadcrumb['itemListElement']
                self.assertEqual([item['position'] for item in crumbs], [1, 2, 3])
                self.assertEqual(crumbs[-1]['item'], f'https://rf-sonne.com/products/{slug}/')

    def test_images_are_uploaded(self):
        for slug in PAGES:
            with self.subTest(page=slug):
                urls = set(
                    re.findall(
                        r'https://rf-sonne\.com/wp-content/uploads/[^"\'\s)]+',
                        read(slug),
                    )
                )
                self.assertTrue(urls)
                self.assertEqual(urls - MEDIA_URLS, set(), 'image URL missing from upload log')

    def test_internal_links_resolve(self):
        known = WP_ROUTES | {'/products', '/products/', '/contact', '/request-a-quote', '/'}
        for slug in PAGES:
            with self.subTest(page=slug):
                source = read(slug)
                for href in re.findall(r'href="(/[^"#]*)', source):
                    route = href.rstrip('/') or '/'
                    self.assertIn(route, known, f'unknown internal route {href} on {slug}')

    def test_no_unreviewed_claims(self):
        for slug in PAGES:
            with self.subTest(page=slug):
                source = read(slug)
                self.assertNotIn('military', source.lower())
                for pattern in FORBIDDEN:
                    self.assertIsNone(pattern.search(source), pattern.pattern)

    def test_navigation_and_footer_include_new_lines(self):
        nav = NAV.read_text(encoding='utf-8')
        footer = FOOTER.read_text(encoding='utf-8')
        self.assertIn("'title' => 'Components'", nav)
        self.assertIn("'title' => 'Systems & Active RF'", nav)
        self.assertEqual(nav.count("'label' => 'Antenna Test Systems'"), 1)
        for slug in PAGES:
            with self.subTest(page=slug):
                self.assertIn(f"/products/{slug}/", nav)
                self.assertIn(f"/products/{slug}/", footer)

    def test_hub_and_sitemap_link_new_lines(self):
        hub = read('products')
        sitemap = read('sitemap')
        for slug in PAGES:
            with self.subTest(page=slug):
                self.assertIn(f'href="/products/{slug}/"', hub)
                self.assertIn(f'href="/products/{slug}/"', sitemap)
        self.assertIn('id="systems"', hub)
        self.assertIn('14 pages', sitemap)


if __name__ == '__main__':
    unittest.main()
