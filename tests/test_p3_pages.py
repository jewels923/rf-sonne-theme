import html
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urljoin, urlsplit


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / 'website'
SOURCE_01 = ROOT / 'docs-strategy' / 'source-01.json'
FRAGMENTS_DIR = ROOT / 'docs-strategy' / 'fragments'
INSIGHTS_DIR = ROOT / 'content' / 'insights'
UPLOAD_LOG = ROOT / 'images-upload-log.json'
IMAGES_MANIFEST = ROOT / 'images-manifest.json'
SONNE_CSS = ROOT / 'sonne.css'
RFQ_FRAGMENT = WEBSITE / 'request-a-quote.html'
RFQ_FORM = ROOT / 'cf7' / 'request-a-quote-form.html'
RFQ_MAIL = ROOT / 'cf7' / 'request-a-quote-mail.json'

TARGETS = {
    'home': ('page-01', '/'),
    'products': ('page-02', '/products'),
    'rf-microwave-filters': ('page-03', '/products/rf-microwave-filters'),
    'waveguide-components': ('page-04', '/products/waveguide-components'),
    'rf-combiners': ('page-05', '/products/rf-combiners'),
    'base-station-rf': ('page-06', '/products/base-station-rf'),
    'precision-enclosures': ('page-07', '/products/precision-enclosures'),
    'engineering': ('page-18', '/engineering'),
    'ibs-das-components': ('page-08', '/products/ibs-das-components'),
    'fttx-fiber-distribution': ('page-09', '/products/fttx-fiber-distribution'),
    'rf-accessories': ('page-10', '/products/rf-accessories'),
    'solutions': ('page-11', '/solutions'),
    '5g-base-station': ('page-12', '/solutions/5g-base-station'),
    'microwave-backhaul': ('page-13', '/solutions/microwave-backhaul'),
    'satellite-earth-station': ('page-14', '/solutions/satellite-earth-station'),
    'das-ibs': ('page-15', '/solutions/das-ibs'),
    'fttx': ('page-16', '/solutions/fttx'),
    'data-center-enclosures': ('page-17', '/solutions/data-center-enclosures'),
    'custom-rf-design': ('page-19', '/engineering/custom-rf-design'),
    'npi': ('page-20', '/engineering/npi'),
    'testing-quality': ('page-21', '/engineering/testing-quality'),
    'manufacturing': ('page-22', '/engineering/manufacturing'),
    'rfq-guide': ('page-25', '/resources/rfq-guide'),
    'faq': ('page-26', '/resources/faq'),
    'datasheets': ('page-27', '/resources/datasheets'),
    'about': ('page-28', '/about'),
    'factory': ('page-29', '/about/factory'),
    'contact': ('page-30', '/contact'),
}
WRAPPERS = {
    'home': 'sn-home',
    'products': 'sn-products',
    'rf-microwave-filters': 'sn-filters',
    'waveguide-components': 'sn-waveguide',
    'rf-combiners': 'sn-combiners',
    'base-station-rf': 'sn-base-station',
    'precision-enclosures': 'sn-enclosures',
    'antenna-test-systems': 'sn-test',
    'switch-matrices': 'sn-sw',
    'tr-modules': 'sn-trm',
    'passive-microwave-components': 'sn-pmc',
    'rf-front-ends': 'sn-rfe',
    'engineering': 'sn-engineering',
    'request-a-quote': 'sn-rfq',
    'ibs-das-components': 'sn-ibs-das',
    'fttx-fiber-distribution': 'sn-fttx-products',
    'rf-accessories': 'sn-accessories',
    'solutions': 'sn-solutions',
    '5g-base-station': 'sn-sol-5g',
    'microwave-backhaul': 'sn-sol-backhaul',
    'satellite-earth-station': 'sn-sol-satellite',
    'das-ibs': 'sn-sol-das',
    'fttx': 'sn-sol-fttx',
    'data-center-enclosures': 'sn-sol-enclosures',
    'custom-rf-design': 'sn-custom-rf',
    'npi': 'sn-npi',
    'testing-quality': 'sn-testing',
    'manufacturing': 'sn-manufacturing',
    'rfq-guide': 'sn-rfq-guide',
    'faq': 'sn-faq-hub',
    'datasheets': 'sn-datasheets',
    'about': 'sn-about',
    'factory': 'sn-factory',
    'contact': 'sn-contact',
    'thank-you': 'sn-thank-you',
    'terms-of-service': 'sn-terms',
    'privacy-policy': 'sn-privacy',
    'sitemap': 'sn-sitemap',
}
LEGACY_MARKERS = ('julong', 'wxkntest', 'sunglasses', 'sports eyewear')
# Rank Math owns the page/site entity graph. Fragments keep only entities
# that Rank Math does not emit: Product, FAQPage and the page breadcrumb.
RANK_MATH_OWNED_SCHEMA_TYPES = {
    'WebPage',
    'AboutPage',
    'ContactPage',
    'CollectionPage',
    'Organization',
    'WebSite',
}
FRAGMENT_SCHEMA_TYPES = {'Product', 'FAQPage', 'BreadcrumbList'}
VERIFIED_URL_PREFIX = 'https://rf-sonne.com/wp-content/uploads/'
RFQ_SITE_URL = 'https://rf-sonne.com/request-a-quote/'
RFQ_H1 = 'Request a Custom RF or Enclosure Quote'
RFQ_H2S = (
    'Start with Your Product Line and Project Basics',
    'Add the Specifications Engineers Need to Review',
    'Upload Band Plans and Drawings with Clear Confidentiality Context',
    'Review Your RFQ and the Next Steps before Submitting',
    'RFQ Submission FAQs',
    'Submit What You Know and Let Engineering Identify the Gaps',
)
RFQ_PRODUCT_LINES = (
    'RF Filters',
    'Waveguide & Microwave',
    'Combiners & Base Station RF',
    'Precision Enclosures',
    'Other / Not Sure',
)
RFQ_PROJECT_STAGES = (
    'Concept / Feasibility',
    'Prototype',
    'Qualification',
    'Pilot',
    'Mass Production',
    'Replacement / Upgrade',
)
RFQ_FILE_PURPOSES = (
    'Band Plan',
    'RF Specification',
    '2D Drawing',
    '3D CAD',
    'Test Requirement',
    'Other',
)
RFQ_FILE_TYPES = 'pdf|step|stp|dxf|xlsx|csv|zip|png|jpg'
CONTACT_TOPICS = (
    'RF and microwave',
    'Waveguide components',
    'Combiners and base-station RF',
    'Precision enclosures',
    'Factory visit',
    'Other / not sure',
)
RFQ_REQUIRED_FIELDS = {
    'your-name',
    'your-email',
    'your-company',
    'product-line',
    'application',
    'project-stage',
    'consent',
}
RFQ_OPTIONAL_FIELDS = {
    'your-phone',
    'country',
    'sample-quantity',
    'expected-volume',
    'target-date',
    'confidentiality-discussion',
    'confidentiality-notes',
}
RFQ_SPEC_FIELDS = {
    'RF Filters': (
        'filter-frequency',
        'filter-bandwidth',
        'filter-insertion-loss',
        'filter-return-loss',
        'filter-rejection',
        'filter-power-pim',
        'filter-interface',
    ),
    'Waveguide & Microwave': (
        'waveguide-frequency',
        'waveguide-size',
        'waveguide-polarization',
        'waveguide-ports',
        'waveguide-loss-power',
        'waveguide-interface',
    ),
    'Combiners & Base Station RF': (
        'combiner-band-plan',
        'combiner-ports',
        'combiner-isolation',
        'combiner-pim',
        'combiner-power',
        'combiner-interface',
    ),
    'Precision Enclosures': (
        'enclosure-material',
        'enclosure-dimensions',
        'enclosure-tolerances',
        'enclosure-surface',
        'enclosure-thermal',
        'enclosure-protection',
        'enclosure-assembly',
    ),
    'Other / Not Sure': ('other-specifications',),
}
RFQ_FAQS = (
    (
        'Can I request a quote without complete specifications?',
        'Yes. Submit the product line, application, project stage and the specifications you already know, then mark uncertain fields as unknown. Engineering can use that information to identify missing inputs and clarify the next step. A complete RFQ is more likely to receive initial engineering feedback in about 24 hours; a formal quote requires sufficient technical and commercial information.',
    ),
    (
        'What frequency range can I include in an RFQ?',
        "SONNE's core production range is DC to 40 GHz. Selected custom microwave and waveguide projects may reach 110 GHz, depending on topology and verification. Include your required bands, bandwidth and performance targets so engineering can assess feasibility. The upper frequency statement is not a blanket commitment for every component or design.",
    ),
    (
        'What files should I upload with my RFQ?',
        "Upload the files that define your requirement: a band plan, RF specification, 2D drawing, 3D CAD or test requirements as applicable. Identify each file's purpose and revision where known. If the material is sensitive, you can request a confidentiality discussion first and submit only a non-sensitive summary until the exchange arrangements are confirmed.",
    ),
    (
        'Does selecting the confidentiality option mean an NDA is accepted?',
        'No. The option tells SONNE that confidentiality should be discussed before sensitive material is exchanged. It does not mean a universal NDA has been accepted or define its scope. Describe your requirement and avoid uploading sensitive files until the appropriate project-specific arrangement has been confirmed by both parties.',
    ),
    (
        'Will I receive a firm price and delivery date within 24 hours?',
        'Not necessarily. The approximately 24-hour guideline refers to initial engineering feedback for a complete RFQ, not a guaranteed firm quotation or delivery commitment. Pricing and timing require review of the design, quantities, processes and capacity. The fastest approximately two-week reference applies only to prototyping in suitable cases, while mass-production timing is confirmed per project.',
    ),
)
RFQ_SENSITIVE_MARKERS = (
    'w.secrets',
    'app_password',
    'sync_auth_token',
    'trans.php',
    'hostinger_bypass',
    'Authorization: Basic',
)


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


SOURCE_PAGES = load_json(SOURCE_01)
SOURCE_BY_ID = {page['id']: page for page in SOURCE_PAGES}
FRAGMENT_PAGES = {}
for fragment_path in sorted(FRAGMENTS_DIR.glob('*.json')):
    fragment_data = load_json(fragment_path)
    if isinstance(fragment_data, list):
        FRAGMENT_PAGES.update({page['id']: page for page in fragment_data})

UPLOADS = load_json(UPLOAD_LOG)
MANIFEST = load_json(IMAGES_MANIFEST)
MANIFEST_BY_FILE = {image['file']: image for image in MANIFEST}
VERIFIED_MEDIA_URLS = {item['url'] for item in UPLOADS.values()}
MEDIA_BY_URL = {
    upload['url']: MANIFEST_BY_FILE[filename]
    for filename, upload in UPLOADS.items()
    if filename in MANIFEST_BY_FILE
}
VALID_ROUTES = set()
for source_page in SOURCE_PAGES:
    source_path = urlsplit(source_page['url']).path
    VALID_ROUTES.add(source_path if source_path == '/' else source_path.rstrip('/'))
for post_path in INSIGHTS_DIR.glob('*.html'):
    VALID_ROUTES.add(f'/resources/insights/{post_path.stem}')


def normalize_text(value):
    if not isinstance(value, str):
        return ''
    text = value.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
    text = ' '.join(text.split())
    return re.sub(r'\s+([,.;:!?])', r'\1', text)


def expected_h1(page_id):
    lines = SOURCE_BY_ID[page_id]['tdk'].splitlines()
    return lines[lines.index('H1') + 1].strip()


def normalize_route(url):
    path = urlsplit(url).path or '/'
    return path if path == '/' else path.rstrip('/')


NEW_PRODUCT_LINE_FILES = {
    'antenna-test-systems.html',
    'switch-matrices.html',
    'tr-modules.html',
    'passive-microwave-components.html',
    'rf-front-ends.html',
}

FORBIDDEN_CLAIM_PATTERNS = (
    re.compile(
        r'\b(?:MOQ|minimum order|payment terms|warranty|money[- ]back|NDA)\b',
        re.IGNORECASE,
    ),
    re.compile(
        r'\b(?:is|are|fully|officially)\s+(?:certified|guaranteed)\b',
        re.IGNORECASE,
    ),
    re.compile(
        r'\b(?:certified|guaranteed)\s+(?:for|to|by)\b',
        re.IGNORECASE,
    ),
    re.compile(
        r'\b(?:certified|guaranteed)\s+(?:\w+\s+){0,3}'
        r'(?:performance|compliance|rating|coverage|operation|product|enclosure|filter|duplexer)\b',
        re.IGNORECASE,
    ),
    re.compile(
        r'\b(?:IP\d{2}|N28|N78|EMC|RoHS|REACH|salt[- ]spray)\b'
        r'[^.]{0,60}\b(?:certified|guaranteed)\b',
        re.IGNORECASE,
    ),
    re.compile(r'\bcompliant\s+for\s+every\b', re.IGNORECASE),
    re.compile(
        r'\b(?:tested|verified|proven)\s+for\s+\d+\s+(?:hours|cycles|days)\b',
        re.IGNORECASE,
    ),
    re.compile(r'\bguaranteed\b[^.]{0,80}\bfor\s+every\b', re.IGNORECASE),
)


def forbidden_claim_matches(text):
    matches = []
    for pattern in FORBIDDEN_CLAIM_PATTERNS:
        matches.extend(match.group(0) for match in pattern.finditer(text))
    return matches


CF7_TAG_PATTERN = re.compile(r'\[([a-z][a-z0-9_-]*)(\*)?((?:\s+[^\]]*)?)\]', re.IGNORECASE)
CF7_VALUE_PAIR_KEYS = {
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
}


def strip_tags(value):
    return html.unescape(re.sub(r'<[^>]+>', ' ', value))


def visible_copy(value):
    value = re.sub(r'<script\b.*?</script>', ' ', value, flags=re.DOTALL | re.IGNORECASE)
    value = re.sub(r'<style\b.*?</style>', ' ', value, flags=re.DOTALL | re.IGNORECASE)
    value = CF7_TAG_PATTERN.sub(' ', value)
    return normalize_text(strip_tags(value))


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


def parse_cf7_tag(match):
    basetype = match.group(1).lower()
    # CF7 6 registers only the plain `radio` tag, and radio groups always validate as required.
    required = bool(match.group(2)) or basetype == 'radio'
    tokens = _cf7_tokens(match.group(3).strip())
    if basetype == 'submit':
        return {
            'type': basetype,
            'required': required,
            'name': '',
            'options': {},
            'values': [text for text, quoted in tokens if quoted],
            'flags': set(),
            'raw': match.group(0),
        }
    if not tokens:
        return None
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
        elif (
            index + 1 < len(tokens)
            and tokens[index + 1][1]
            and text in CF7_VALUE_PAIR_KEYS
        ):
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
        'raw': match.group(0),
    }


def parse_cf7_tags(source):
    tags = []
    for match in CF7_TAG_PATTERN.finditer(source):
        tag = parse_cf7_tag(match)
        if tag is not None:
            tags.append(tag)
    return tags


class FragmentCollector(HTMLParser):
    """Collect the fragment structure without browser or third-party parsers."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1s = []
        self._h1_parts = None
        self.h2s = []
        self._h2_parts = None
        self.section_count = 0
        self.ids = set()
        self.label_texts = {}
        self.table_regions = []
        self.wrappers = []
        self.top_level_wrappers = []
        self.content_outside_wrapper = False
        self._stack = []
        self.styles = []
        self._style_parts = None
        self.jsonld_blocks = []
        self._jsonld_parts = None
        self.images = []
        self.media_urls = []
        self.anchors = []
        self.table_anchors = []
        self._anchor_parts = None
        self.faqs = []
        self.faq_links = []
        self.faq_tail_links = []
        self.faq_groups = []
        self.text_parts = []
        self.attribute_texts = []
        self._faq = None
        self._in_summary = False
        self._faq_group = None
        self._faq_group_level = None
        self._faq_group_heading_parts = None
        self._open_table_regions = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get('id'):
            self.ids.add(attributes['id'])
        for text_attribute in ('alt', 'title', 'aria-label'):
            if attributes.get(text_attribute, '').strip():
                self.attribute_texts.append(attributes[text_attribute].strip())
        if (
            self._faq is not None
            and not self._in_summary
            and tag in {'img', 'svg', 'video', 'audio', 'table', 'ul', 'ol'}
        ):
            self._faq['tail_is_link'] = False
        classes = attributes.get('class', '').split()
        if 'sn-table-wrap' in classes:
            region = dict(attributes)
            region['contains_table'] = False
            self.table_regions.append(region)
            self._open_table_regions.append([region, 0])
        if tag == 'div' and any(name.endswith('__faq-group') for name in classes):
            self._faq_group = {'heading': '', 'count': 0}
            self._faq_group_level = len(self._stack) + 1
            self.faq_groups.append(self._faq_group)
        if tag == 'h3' and self._faq_group is not None:
            self._faq_group_heading_parts = []
        if tag == 'section':
            self.section_count += 1
        recognized = [
            class_name for class_name in classes
            if class_name in set(WRAPPERS.values())
        ]
        self.wrappers.extend(recognized)

        is_top_level = not self._stack
        inside_nonrendered = any(item[0] in {'style', 'script'} for item in self._stack)
        current_wrappers = []
        if is_top_level:
            for class_name in recognized:
                wrapper = {'class': class_name, 'has_content': False}
                self.top_level_wrappers.append(wrapper)
                current_wrappers.append(wrapper)
        if tag not in {'style', 'script'} and not inside_nonrendered:
            if is_top_level:
                if not current_wrappers:
                    self.content_outside_wrapper = True
            else:
                self._mark_rendered_content()

        if tag == 'h1' and self._h1_parts is None:
            self._h1_parts = []
        elif tag == 'h2' and self._h2_parts is None:
            self._h2_parts = []
        elif tag == 'style':
            self._style_parts = []
        elif tag == 'script':
            if attributes.get('type', '').strip().lower() == 'application/ld+json':
                self._jsonld_parts = []
        elif tag == 'img':
            self.images.append(attributes)
            if attributes.get('src', '').strip():
                self.media_urls.append(attributes['src'].strip())
            self._collect_srcset(attributes)
        elif tag == 'source':
            self._collect_srcset(attributes)
        elif tag == 'a':
            anchor = dict(attributes)
            self.anchors.append(anchor)
            if self._open_table_regions:
                self.table_anchors.append(anchor)
            self._anchor_parts = []
            if self._faq is not None:
                self._faq['links'].append(attributes.get('href', ''))
                self._faq['tail_is_link'] = False
        elif tag == 'details':
            if self._faq_group is not None:
                self._faq_group['count'] += 1
            self._faq = {
                'summary': [],
                'answer': [],
                'links': [],
                'tail_is_link': False,
            }
            self._in_summary = False
        elif tag == 'summary' and self._faq is not None:
            self._in_summary = True

        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                       'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            if tag == 'table':
                for region, _depth in self._open_table_regions:
                    region['contains_table'] = True
            self._stack.append((tag, current_wrappers, attributes.get('id')))
            for entry in self._open_table_regions:
                entry[1] += 1

    def handle_endtag(self, tag):
        if tag == 'h1' and self._h1_parts is not None:
            self.h1s.append(normalize_text(' '.join(self._h1_parts)))
            self._h1_parts = None
        elif tag == 'h2' and self._h2_parts is not None:
            self.h2s.append(normalize_text(' '.join(self._h2_parts)))
            self._h2_parts = None
        elif tag == 'style' and self._style_parts is not None:
            self.styles.append(''.join(self._style_parts))
            self._style_parts = None
        elif tag == 'script' and self._jsonld_parts is not None:
            self.jsonld_blocks.append(''.join(self._jsonld_parts))
            self._jsonld_parts = None
        elif tag == 'a' and self._anchor_parts is not None:
            self.anchors[-1]['text'] = normalize_text(' '.join(self._anchor_parts))
            self._anchor_parts = None
            if self._faq is not None and not self._in_summary:
                self._faq['tail_is_link'] = True
        elif tag == 'h3' and self._faq_group_heading_parts is not None:
            self._faq_group['heading'] = normalize_text(
                ' '.join(self._faq_group_heading_parts)
            )
            self._faq_group_heading_parts = None
        elif tag == 'summary':
            self._in_summary = False
        elif tag == 'details' and self._faq is not None:
            self.faqs.append((
                normalize_text(' '.join(self._faq['summary'])),
                normalize_text(' '.join(self._faq['answer'])),
            ))
            self.faq_links.append(self._faq['links'])
            self.faq_tail_links.append(self._faq['tail_is_link'])
            self._faq = None
            self._in_summary = False

        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                       'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            for entry in self._open_table_regions:
                entry[1] -= 1
            self._open_table_regions = [
                entry for entry in self._open_table_regions if entry[1] > 0
            ]

        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                break

        if (
            self._faq_group is not None
            and self._faq_group_level is not None
            and len(self._stack) < self._faq_group_level
        ):
            self._faq_group = None
            self._faq_group_level = None

    def handle_data(self, data):
        inside_nonrendered = any(
            item[0] in {'style', 'script'} for item in self._stack
        )
        if inside_nonrendered:
            if self._style_parts is not None:
                self._style_parts.append(data)
            if self._jsonld_parts is not None:
                self._jsonld_parts.append(data)
            return
        if data.strip():
            self._mark_rendered_content()
            self.text_parts.append(data)
        for tag, _wrappers, element_id in self._stack:
            if element_id and tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'caption'}:
                self.label_texts.setdefault(element_id, []).append(data)
        if self._h1_parts is not None:
            self._h1_parts.append(data)
        if self._h2_parts is not None:
            self._h2_parts.append(data)
        if self._anchor_parts is not None:
            self._anchor_parts.append(data)
        elif self._faq is not None and data.strip():
            self._faq['tail_is_link'] = False
        if self._faq_group_heading_parts is not None:
            self._faq_group_heading_parts.append(data)
        if self._faq is not None:
            key = 'summary' if self._in_summary else 'answer'
            self._faq[key].append(data)

    def _mark_rendered_content(self):
        active_wrappers = [
            wrapper
            for _tag, wrappers, _element_id in self._stack
            for wrapper in wrappers
        ]
        if active_wrappers:
            for wrapper in active_wrappers:
                wrapper['has_content'] = True
        else:
            self.content_outside_wrapper = True

    def _collect_srcset(self, attributes):
        for candidate in attributes.get('srcset', '').split(','):
            url = candidate.strip().split()
            if url:
                self.media_urls.append(url[0])


def collect(text):
    parser = FragmentCollector()
    parser.feed(text)
    parser.close()
    return parser


def count_h1(text):
    return len(collect(text).h1s)


def iter_jsonld_objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_jsonld_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_jsonld_objects(child)


def iter_top_level_jsonld_objects(document):
    if isinstance(document, list):
        for item in document:
            yield from iter_top_level_jsonld_objects(item)
    elif isinstance(document, dict):
        graph = document.get('@graph')
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict):
                    yield item
        else:
            yield document


def schema_types(value):
    schema_type = value.get('@type', [])
    if isinstance(schema_type, str):
        return {schema_type}
    if isinstance(schema_type, list):
        return {item for item in schema_type if isinstance(item, str)}
    return set()


def jsonld_strings(block):
    """Yield every string value in one JSON-LD document, including string arrays."""
    def walk(value):
        if isinstance(value, dict):
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)
        elif isinstance(value, str):
            yield value

    return walk(json.loads(block))


def iter_css_rules(css):
    """Yield qualified-rule selectors and declarations, including in media queries."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)

    def delimiter(block, start):
        quote = None
        escaped = False
        parentheses = 0
        for index in range(start, len(block)):
            char = block[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in ('"', "'"):
                quote = char
            elif char == '(':
                parentheses += 1
            elif char == ')':
                parentheses = max(0, parentheses - 1)
            elif parentheses == 0 and char in ('{', ';'):
                return index, char
        return None, None

    def closing_brace(block, opening):
        depth = 1
        quote = None
        escaped = False
        for index in range(opening + 1, len(block)):
            char = block[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in ('"', "'"):
                quote = char
            elif char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return index
        raise AssertionError('Unclosed CSS rule')

    def parse(block):
        position = 0
        while position < len(block):
            while position < len(block) and block[position].isspace():
                position += 1
            if position >= len(block):
                break
            index, token = delimiter(block, position)
            if index is None:
                break
            prelude = block[position:index].strip()
            if token == ';':
                position = index + 1
                continue
            end = closing_brace(block, index)
            body = block[index + 1:end]
            if prelude.startswith('@'):
                at_rule = prelude[1:].split(None, 1)[0].lower()
                if at_rule in {'media', 'supports', 'layer', 'container'}:
                    yield from parse(body)
            elif prelude:
                yield prelude, body
            position = end + 1

    yield from parse(css)


def iter_css_selectors(css):
    """Yield qualified-rule selectors, descending into conditional group rules."""
    for selector, _declarations in iter_css_rules(css):
        yield selector


def css_media_block(css, media_query):
    """Return the declaration body of the first matching @media block."""
    match = re.search(r'@media\s+' + re.escape(media_query) + r'\b\s*\{', css)
    if not match:
        return ''
    depth = 1
    index = match.end()
    while index < len(css) and depth:
        if css[index] == '{':
            depth += 1
        elif css[index] == '}':
            depth -= 1
        index += 1
    return css[match.end():index - 1] if depth == 0 else ''


def css_declarations_for_selector(css, target_selector):
    """Return the last declared values for an exact selector in source order."""
    declarations = {}
    for selector_list, body in iter_css_rules(css):
        if target_selector not in split_selector_list(selector_list):
            continue
        for declaration in body.split(';'):
            property_name, separator, value = declaration.partition(':')
            if separator:
                declarations[property_name.strip()] = value.strip()
    return declarations


def css_without_media_queries(css):
    """Return CSS with @media blocks removed, preserving base declarations."""
    result = []
    index = 0
    while True:
        match = re.search(r'@media\b[^{]*\{', css[index:])
        if not match:
            result.append(css[index:])
            break
        start = index + match.start()
        result.append(css[index:start])
        depth = 1
        position = index + match.end()
        while position < len(css) and depth:
            if css[position] == '{':
                depth += 1
            elif css[position] == '}':
                depth -= 1
            position += 1
        index = position
    return ''.join(result)


def split_selector_list(selector_list):
    selectors = []
    start = 0
    parentheses = 0
    for index, char in enumerate(selector_list):
        if char == '(':
            parentheses += 1
        elif char == ')':
            parentheses = max(0, parentheses - 1)
        elif char == ',' and parentheses == 0:
            selectors.append(selector_list[start:index].strip())
            start = index + 1
    selectors.append(selector_list[start:].strip())
    return selectors


def selector_is_wrapper_rooted(selector, wrapper):
    """Require the styled subject to be the wrapper or its descendant."""
    selector = selector.strip()
    if not selector:
        return False

    quote = None
    escaped = False
    parentheses = 0
    brackets = 0
    root_compound = selector
    first_combinator = None
    for index, char in enumerate(selector):
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
        elif char == '(':
            parentheses += 1
        elif char == ')':
            parentheses = max(0, parentheses - 1)
        elif char == '[':
            brackets += 1
        elif char == ']':
            brackets = max(0, brackets - 1)
        elif parentheses == 0 and brackets == 0 and char in '>+~':
            root_compound = selector[:index].strip()
            first_combinator = char
            break
        elif parentheses == 0 and brackets == 0 and char.isspace():
            root_compound = selector[:index].strip()
            following = index
            while following < len(selector) and selector[following].isspace():
                following += 1
            if following < len(selector) and selector[following] in '>+~':
                first_combinator = selector[following]
            else:
                first_combinator = ' '
            break
    if first_combinator in {'+', '~'}:
        return False
    if re.search(r':has\(\s*[+~]', root_compound, re.IGNORECASE):
        return False

    class_pattern = re.compile(rf'\.{re.escape(wrapper)}(?![\w-])')
    quote = None
    escaped = False
    parentheses = 0
    brackets = 0
    index = 0
    while index < len(root_compound):
        char = root_compound[index]
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in ('"', "'"):
            quote = char
        elif char == '(':
            parentheses += 1
        elif char == ')':
            parentheses = max(0, parentheses - 1)
        elif char == '[':
            brackets += 1
        elif char == ']':
            brackets = max(0, brackets - 1)
        elif parentheses == 0 and brackets == 0 and char == '.':
            if class_pattern.match(root_compound, index):
                return True
        index += 1

    quote = None
    escaped = False
    parentheses = 0
    brackets = 0
    index = 0
    while index < len(root_compound):
        char = root_compound[index]
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in ('"', "'"):
            quote = char
            index += 1
            continue
        if char == '[':
            brackets += 1
        elif char == ']':
            brackets = max(0, brackets - 1)
        elif char == '(':
            parentheses += 1
        elif char == ')':
            parentheses = max(0, parentheses - 1)
        elif parentheses == 0 and brackets == 0 and char == ':':
            match = re.match(r':(?:is|where|matches)\(', root_compound[index:], re.IGNORECASE)
            if match:
                opening = index + match.end() - 1
                depth = 1
                inner_quote = None
                inner_escaped = False
                end = opening + 1
                while end < len(root_compound) and depth:
                    inner = root_compound[end]
                    if inner_quote:
                        if inner_escaped:
                            inner_escaped = False
                        elif inner == '\\':
                            inner_escaped = True
                        elif inner == inner_quote:
                            inner_quote = None
                    elif inner in ('"', "'"):
                        inner_quote = inner
                    elif inner == '(':
                        depth += 1
                    elif inner == ')':
                        depth -= 1
                    end += 1
                if depth:
                    return False
                alternatives = split_selector_list(root_compound[opening + 1:end - 1])
                return bool(alternatives) and all(
                    selector_is_wrapper_rooted(alternative, wrapper)
                    for alternative in alternatives
                )
        index += 1
    return False


class P3SharedChromeTests(unittest.TestCase):
    """Validate the SONNE design layer and chrome shared by every P3 page."""

    @classmethod
    def setUpClass(cls):
        cls.sonne_path = ROOT / 'sonne.css'
        cls.sonne_css = cls.sonne_path.read_text(encoding='utf-8') if cls.sonne_path.is_file() else ''
        cls.functions = (ROOT / 'functions.php').read_text(encoding='utf-8')
        cls.contact = (ROOT / 'template-parts' / 'data' / 'site-contact.php').read_text(encoding='utf-8')
        cls.navigation = (ROOT / 'template-parts' / 'data' / 'header-navigation.php').read_text(encoding='utf-8')
        cls.footer_groups = (ROOT / 'template-parts' / 'data' / 'footer-groups.php').read_text(encoding='utf-8')
        cls.header = (ROOT / 'template-parts' / 'header.php').read_text(encoding='utf-8')
        cls.footer = (ROOT / 'template-parts' / 'footer.php').read_text(encoding='utf-8')
        cls.header_script = (ROOT / 'assets' / 'site-header.js').read_text(encoding='utf-8')
        cls.chrome = '\n'.join((
            cls.contact,
            cls.navigation,
            cls.footer_groups,
            cls.header,
            cls.footer,
        ))

    def test_sonne_design_layer_defines_shared_contract(self):
        self.assertTrue(self.sonne_path.is_file(), 'Missing shared sonne.css design layer')
        for selector in ('.sn-hero', '.sn-btn', '.sn-container', '.sn-section', '.sn-breadcrumbs'):
            with self.subTest(selector=selector):
                self.assertIn(selector, self.sonne_css)
        for token in ('--sn-graphite', '--sn-navy', '--sn-cyan', '--sn-font-body', '--sn-font-mono'):
            with self.subTest(token=token):
                self.assertIn(token, self.sonne_css)
        self.assertIn(':focus-visible', self.sonne_css)
        self.assertRegex(self.sonne_css, r'min-height:\s*44px')
        self.assertIn('prefers-reduced-motion', self.sonne_css)
        self.assertIn('@media (max-width: 768px)', self.sonne_css)

    def test_table_regions_have_visible_keyboard_focus(self):
        declarations = css_declarations_for_selector(
            self.sonne_css,
            '.sn-table-wrap:focus-visible',
        )
        self.assertEqual('3px solid var(--sn-cyan-dark)', declarations.get('outline'))
        self.assertEqual('3px', declarations.get('outline-offset'))

    def test_mobile_drawer_has_explicit_light_surface_colors(self):
        expected = {
            '.site-mobile-nav__panel': {
                'background': 'var(--sn-light-gray)',
                'color': 'var(--sn-text)',
            },
            '.site-mobile-nav__brand': {'color': 'var(--sn-text)'},
            '.site-mobile-nav__subline': {'color': 'var(--sn-text-muted)'},
            '.site-mobile-nav__link': {'color': 'var(--sn-text)'},
            '.site-mobile-nav__submenu-title': {'color': 'var(--sn-text)'},
            '.site-mobile-nav__submenu a': {'color': 'var(--sn-text-muted)'},
            '.site-mobile-nav__contact a:not(.sn-btn)': {'color': 'var(--sn-text-muted)'},
            '.site-mobile-nav__header': {'border-color': 'var(--sn-mid-gray)'},
            '.site-mobile-nav__item': {'border-color': 'var(--sn-mid-gray)'},
            '.site-mobile-nav__close': {
                'background': 'var(--sn-white)',
                'border-color': 'var(--sn-mid-gray)',
                'color': 'var(--sn-text)',
            },
            '.site-mobile-nav__toggle': {
                'background': 'var(--sn-white)',
                'border-color': 'var(--sn-mid-gray)',
                'color': 'var(--sn-text)',
            },
        }
        for selector, declarations in expected.items():
            for property_name, value in declarations.items():
                with self.subTest(selector=selector, property=property_name):
                    actual = css_declarations_for_selector(self.sonne_css, selector)
                    self.assertEqual(value, actual.get(property_name))

    def test_mobile_drawer_focus_is_visible_on_light_and_dark_chrome(self):
        drawer_focus = css_declarations_for_selector(
            self.sonne_css,
            '.site-mobile-nav__panel :focus-visible',
        )
        header_focus = css_declarations_for_selector(
            self.sonne_css,
            '.site-header-shell :focus-visible',
        )
        self.assertEqual('var(--sn-cyan-dark)', drawer_focus.get('outline-color'))
        self.assertEqual('var(--sn-accent-on-dark)', header_focus.get('outline-color'))

        def luminance(hex_color):
            channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
            return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

        def token_hex(name):
            match = re.search(rf'{name}:\s*([^;]+);', self.sonne_css)
            self.assertIsNotNone(match, name)
            value = match.group(1).strip()
            if value.startswith('var('):
                return token_hex(value[4:-1].strip())
            self.assertRegex(value, r'^#[0-9a-fA-F]{6}$')
            return value

        tokens = {}
        for token in ('--sn-cyan-dark', '--sn-light-gray', '--sn-accent-on-dark', '--sn-ink-deep'):
            tokens[token] = token_hex(token)
        dark_cyan = luminance(tokens['--sn-cyan-dark'])
        light_surface = luminance(tokens['--sn-light-gray'])
        contrast = (light_surface + 0.05) / (dark_cyan + 0.05)
        self.assertGreaterEqual(contrast, 3.0)
        header_focus_contrast = (luminance(tokens['--sn-accent-on-dark']) + 0.05) / (luminance(tokens['--sn-ink-deep']) + 0.05)
        self.assertGreaterEqual(header_focus_contrast, 3.0)

    def test_mobile_logo_uses_auto_height_at_its_constrained_width(self):
        logo = css_declarations_for_selector(self.sonne_css, 'body .site-branding__logo')
        self.assertEqual('124px', logo.get('width'))
        self.assertEqual('124px', logo.get('max-width'))
        self.assertEqual('auto !important', logo.get('height'))

    def test_footer_logo_keeps_intrinsic_ratio_at_its_capped_width(self):
        main_css = (ROOT / 'main.css').read_text(encoding='utf-8')
        logo = css_declarations_for_selector(main_css, '.site-footer__brand-logo')
        self.assertEqual('auto', logo.get('height'))
        self.assertEqual('180px', logo.get('max-width'))
        self.assertEqual('54px', logo.get('max-height'))

    def test_mobile_legacy_table_cells_keep_inline_content_in_one_value_cell(self):
        self.assertRegex(
            self.sonne_css,
            r'\.sn-legacy-record \.sn-table tbody td \{\s*display: table;',
        )
        self.assertRegex(
            self.sonne_css,
            r'\.sn-legacy-record \.sn-table tbody td::before \{\s*content: attr\(data-label\);\s*display: table-cell;',
        )

    def test_mega_preview_image_fills_its_frame(self):
        card = css_declarations_for_selector(self.sonne_css, 'body .site-nav__mega-preview')
        image = css_declarations_for_selector(self.sonne_css, 'body .site-nav__mega-preview img')
        self.assertEqual('var(--sn-navy-deep)', card.get('background'))
        self.assertEqual('cover', image.get('object-fit'))
        self.assertEqual('0', image.get('padding'))

    def test_sitewide_breadcrumb_and_eyebrow_labels_are_enlarged(self):
        breadcrumbs = css_declarations_for_selector(self.sonne_css, '.sn-breadcrumbs')
        eyebrow = css_declarations_for_selector(self.sonne_css, 'body [class$="__eyebrow"][class]')
        self.assertEqual('0.9375rem', breadcrumbs.get('font-size'))
        self.assertEqual('0.9375rem', eyebrow.get('font-size'))

    def test_sonne_stylesheet_loads_after_main_and_widget_is_bypassed(self):
        main_version = "child_theme_asset_version('main.css')"
        sonne_version = "child_theme_asset_version('sonne.css')"
        self.assertIn(main_version, self.functions)
        self.assertIn(sonne_version, self.functions)
        self.assertLess(self.functions.index(main_version), self.functions.index(sonne_version))
        self.assertIn("array('child-theme-main-css')", self.functions)
        self.assertNotIn('whatsapp-widget.php', self.functions)

    def test_fonts_are_self_hosted_without_a_google_fonts_import(self):
        main_css = (ROOT / 'main.css').read_text(encoding='utf-8')
        theme_header = (ROOT / 'header.php').read_text(encoding='utf-8')
        self.assertNotIn('fonts.googleapis.com', main_css)
        self.assertNotIn('fonts.googleapis.com', theme_header)
        self.assertIn("assets/css/sonne-fonts.css", self.functions)
        self.assertIn("'/assets/fonts/'", theme_header)
        self.assertIn('archivo-latin-var.woff2', theme_header)

    def test_greek_glyphs_render_from_the_self_hosted_family(self):
        fonts_css = (ROOT / 'assets' / 'css' / 'sonne-fonts.css').read_text(encoding='utf-8')
        self.assertTrue((ROOT / 'assets' / 'fonts' / 'plex-sans-greek-var.woff2').is_file())
        faces = re.findall(r'@font-face \{[^}]*plex-sans-greek-var\.woff2[^}]*\}', fonts_css)
        families = {re.search(r"font-family: '([^']+)'", face).group(1) for face in faces}
        self.assertEqual(families, {'IBM Plex Sans', 'IBM Plex Mono'})
        covered = set()
        for face in faces:
            for token in re.search(r'unicode-range: ([^;]+);', face).group(1).split(','):
                token = token.strip().lower().replace('u+', '')
                start, _, end = token.partition('-')
                covered.update(range(int(start, 16), int(end or start, 16) + 1))
        greek = set()
        sources = list((ROOT / 'website').glob('*.html')) + list((ROOT / 'content' / 'insights').glob('*.html'))
        for path in sources:
            greek.update(ch for ch in path.read_text(encoding='utf-8') if 0x0370 <= ord(ch) <= 0x03FF)
        self.assertTrue(greek)
        self.assertEqual(sorted(greek - {chr(cp) for cp in covered}), [])

    def test_nav_typography_is_owned_by_the_sonne_layer(self):
        main_css = (ROOT / 'main.css').read_text(encoding='utf-8')
        self.assertNotIn('.site-nav__link, .main-navigation a {', main_css)
        legacy_family = css_declarations_for_selector(main_css, '.site-nav__link').get('font-family', '')
        self.assertTrue(legacy_family.startswith('var(--'))
        nav = css_declarations_for_selector(self.sonne_css, 'body .site-nav__link')
        self.assertEqual(nav.get('font-size'), '0.76rem')
        self.assertEqual(nav.get('font-weight'), '600')
        self.assertEqual(nav.get('text-transform'), 'uppercase')

    def test_chrome_uses_confirmed_sonne_brand_contact_and_logo(self):
        self.assertRegex(self.contact, r"'brand_name'\s+=>\s+'SONNE'")
        self.assertRegex(self.contact, r"'company_name'\s+=>\s+'SONNE ELECTRONICS'")
        self.assertRegex(self.contact, r"'email'\s+=>\s+'info@rf-sonne\.com'")
        self.assertIn(UPLOADS['logo-sonne-white.png']['url'], self.contact)
        self.assertIn('SONNE Electronics logo', self.contact)
        for marker in LEGACY_MARKERS + ('eyewear',):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.chrome.lower())
        for unconfirmed in ('whatsapp', 'wechat', 'phone_display', 'social_links', 'street-address'):
            with self.subTest(unconfirmed=unconfirmed):
                self.assertNotIn(unconfirmed, self.chrome.lower())

    def test_navigation_and_footer_use_01_architecture(self):
        required_routes = (
            '/products/',
            '/products/rf-microwave-filters/',
            '/products/waveguide-components/',
            '/products/rf-combiners/',
            '/products/base-station-rf/',
            '/products/precision-enclosures/',
            '/solutions/',
            '/engineering/',
            '/resources/',
            '/about/',
            '/contact/',
            '/request-a-quote/',
        )
        for route in required_routes:
            with self.subTest(route=route):
                self.assertIn(route, self.chrome)
        self.assertNotIn('/contact-us/', self.chrome)
        self.assertNotIn('/about-us/', self.chrome)
        self.assertIn("home_url('/request-a-quote/')", self.header)
        self.assertIn("home_url('/request-a-quote/')", self.footer)

    def test_footer_has_no_cf7_modal_or_contact_link_interception(self):
        for removed in (
            'contact-form-7',
            'do_shortcode',
            'site-footer-inquiry-modal',
            'site-footer-modal',
            'contactCtas',
            'js-footer-quote-open',
            '/contact-us/',
        ):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, self.footer)

    def test_header_script_recognizes_sonne_dark_heroes(self):
        self.assertIn('.sn-hero', self.header_script)

    def test_back_to_top_is_docked_in_footer_on_mobile(self):
        bottom = self.footer.index('site-footer__bottom')
        anchor = self.footer.index('data-back-top')
        footer_end = self.footer.index('</footer>')
        self.assertLess(bottom, anchor)
        self.assertLess(anchor, footer_end)

        preview = (ROOT / 'preview_site.py').read_text(encoding='utf-8')
        self.assertLess(preview.index('site-footer__bottom'), preview.index('data-back-top'))
        self.assertLess(preview.index('data-back-top'), preview.index('</footer>'))

        for name, source in (('footer.php', self.footer), ('preview_site.py', preview)):
            self.assertIn("document.querySelector('.site-footer')", source, name)
            self.assertIn('IntersectionObserver', source, name)
            self.assertIn('footerVisible', source, name)
            self.assertNotIn('&&', source, name)

        main_css = (ROOT / 'main.css').read_text(encoding='utf-8')
        back_top = css_declarations_for_selector(main_css, '.site-footer__back-top')
        self.assertEqual('static', back_top.get('position'))
        self.assertEqual('1', back_top.get('opacity'))
        self.assertEqual('visible', back_top.get('visibility'))
        label = css_declarations_for_selector(main_css, '.site-footer__back-top-label')
        self.assertEqual('inline', label.get('display'))


class P3PageTests(unittest.TestCase):
    maxDiff = None

    def target(self, slug):
        path = WEBSITE / f'{slug}.html'
        self.assertTrue(path.is_file(), f'{slug}: missing target fragment {path.name}')
        if not path.is_file():
            return None, None
        text = path.read_text(encoding='utf-8')
        return text, collect(text)

    def test_source_contracts_are_complete(self):
        self.assertEqual(36, len(SOURCE_PAGES))
        for slug, (page_id, route) in TARGETS.items():
            with self.subTest(contract=slug):
                self.assertIn(page_id, SOURCE_BY_ID)
                self.assertIn(page_id, FRAGMENT_PAGES)
                self.assertEqual(route, SOURCE_BY_ID[page_id]['url'])
                self.assertEqual(route, FRAGMENT_PAGES[page_id]['url'])
                self.assertEqual(expected_h1(page_id), FRAGMENT_PAGES[page_id]['h1'])
                source_schema = SOURCE_BY_ID[page_id]['schema'].splitlines()[1:]
                self.assertEqual(source_schema, FRAGMENT_PAGES[page_id]['schema'])
        for filename, image in MANIFEST_BY_FILE.items():
            with self.subTest(media=filename):
                self.assertTrue(image['alt'].strip())
                self.assertIn(filename, UPLOADS)
                self.assertTrue(UPLOADS[filename]['url'].startswith(VERIFIED_URL_PREFIX))

    def test_contract_page_target_set(self):
        expected = {f'{slug}.html' for slug in TARGETS}
        actual = {
            path.name for path in WEBSITE.glob('*.html')
            if path.stem in TARGETS
        }
        self.assertEqual(28, len(expected))
        self.assertEqual(expected, actual, 'The SONNE contract set must contain all 28 fragments')

    def test_fragment_shell_exact_h1_and_forbidden_markers(self):
        for slug, (page_id, route) in TARGETS.items():
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                self.assertTrue(text.lstrip().startswith('<!-- wp:html -->'), slug)
                self.assertNotRegex(text, r'<(?:html|body|main)(?:\s|>)', slug)
                self.assertNotRegex(text, r'\sstyle\s*=', slug)
                self.assertEqual(count_h1(text), 1, slug)
                self.assertIn(html.escape(expected_h1(page_id), quote=False), text, slug)
                self.assertEqual([expected_h1(page_id)], collector.h1s, slug)
                for marker in LEGACY_MARKERS:
                    self.assertNotIn(marker, text.lower(), f'{slug}: {marker}')

    def test_source_section_sequence_and_h2s(self):
        for slug, (page_id, _route) in TARGETS.items():
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                sections = FRAGMENT_PAGES[page_id]['sections']
                h2_sections = sections[1:] if sections[0]['name'].strip().lower() == 'hero' else sections
                expected_h2s = [normalize_text(section['h2']) for section in h2_sections]
                self.assertEqual(len(sections), collector.section_count, slug)
                self.assertEqual(expected_h2s, collector.h2s, slug)

    def test_exact_wrapper_and_one_scoped_style(self):
        for slug in TARGETS:
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                wrapper = WRAPPERS[slug]
                self.assertEqual([wrapper], collector.wrappers, slug)
                self.assertEqual(
                    [wrapper],
                    [item['class'] for item in collector.top_level_wrappers],
                    f'{slug}: expected one top-level .{wrapper}',
                )
                self.assertEqual(
                    [True],
                    [item['has_content'] for item in collector.top_level_wrappers],
                    f'{slug}: top-level .{wrapper} must contain rendered content',
                )
                self.assertFalse(
                    collector.content_outside_wrapper,
                    f'{slug}: rendered fragment content escapes .{wrapper}',
                )
                self.assertEqual(1, len(collector.styles), slug)
                if len(collector.styles) != 1:
                    continue
                self.assertTrue(collector.styles[0].strip(), slug)
                selectors = [
                    selector
                    for rule in iter_css_selectors(collector.styles[0])
                    for selector in split_selector_list(rule)
                ]
                self.assertTrue(selectors, f'{slug}: style block has no qualified rules')
                unscoped = [
                    selector for selector in selectors
                    if not selector_is_wrapper_rooted(selector, wrapper)
                ]
                self.assertEqual([], unscoped, f'{slug}: selectors escape .{wrapper}')

    def test_verified_media_urls_and_nonempty_alts(self):
        for slug in TARGETS:
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                self.assertTrue(collector.images, f'{slug}: page must use real registry imagery')
                for image in collector.images:
                    src = image.get('src', '').strip()
                    alt = image.get('alt')
                    self.assertIsNotNone(alt, f'{slug}: missing alt on {src}')
                    self.assertTrue(alt and alt.strip(), f'{slug}: empty alt on {src}')
                    self.assertTrue(src.startswith(VERIFIED_URL_PREFIX), f'{slug}: {src}')
                    self.assertIn(src, VERIFIED_MEDIA_URLS, f'{slug}: unverified {src}')
                    self.assertIn(src, MEDIA_BY_URL, f'{slug}: missing manifest entry for {src}')
                    media = MEDIA_BY_URL[src]
                    self.assertEqual(media['alt'], alt, f'{slug}: manifest alt mismatch on {src}')
                    self.assertEqual(str(media['width']), image.get('width'), f'{slug}: width on {src}')
                    self.assertEqual(str(media['height']), image.get('height'), f'{slug}: height on {src}')
                for url in collector.media_urls:
                    self.assertIn(url, VERIFIED_MEDIA_URLS, f'{slug}: unverified {url}')

    def test_jsonld_schema_and_visible_faq_consistency(self):
        for slug, (page_id, route) in TARGETS.items():
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                self.assertTrue(collector.jsonld_blocks, f'{slug}: missing JSON-LD')
                if not collector.jsonld_blocks:
                    continue
                documents = []
                for block in collector.jsonld_blocks:
                    try:
                        documents.append(json.loads(block))
                    except json.JSONDecodeError as error:
                        self.fail(f'{slug}: invalid JSON-LD: {error}')
                objects = [
                    item
                    for document in documents
                    for item in iter_jsonld_objects(document)
                ]
                top_level_objects = [
                    item
                    for document in documents
                    for item in iter_top_level_jsonld_objects(document)
                ]
                actual_types = set().union(*(schema_types(item) for item in top_level_objects))
                expected_types = (
                    set(FRAGMENT_PAGES[page_id]['schema'])
                    - RANK_MATH_OWNED_SCHEMA_TYPES
                )
                self.assertEqual(expected_types, actual_types, f'{slug}: fragment schema drifted from 01')
                self.assertEqual(
                    set(),
                    actual_types & RANK_MATH_OWNED_SCHEMA_TYPES,
                    f'{slug}: Rank Math owns these page entities; the fragment must not repeat them',
                )

                source_faqs = [
                    (normalize_text(faq['question']), normalize_text(faq['answer']))
                    for faq in FRAGMENT_PAGES[page_id]['faqs']
                ]
                self.assertEqual(source_faqs, collector.faqs, f'{slug}: visible FAQs differ from 02')

                faq_pages = [item for item in objects if 'FAQPage' in schema_types(item)]
                if 'FAQPage' in expected_types or faq_pages:
                    self.assertEqual(1, len(faq_pages), f'{slug}: expected one FAQPage')
                    if len(faq_pages) != 1:
                        continue
                    entities = faq_pages[0].get('mainEntity', [])
                    if isinstance(entities, dict):
                        entities = [entities]
                    structured_faqs = []
                    for entity in entities:
                        self.assertIn('Question', schema_types(entity), slug)
                        answer = entity.get('acceptedAnswer', {})
                        self.assertIn('Answer', schema_types(answer), slug)
                        structured_faqs.append((
                            normalize_text(entity.get('name')),
                            normalize_text(answer.get('text')),
                        ))
                    self.assertEqual(collector.faqs, structured_faqs, f'{slug}: FAQ mainEntity mismatch')

    def test_table_regions_are_keyboard_accessible(self):
        for slug in TARGETS:
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                for region in collector.table_regions:
                    self.assertEqual('0', region.get('tabindex'), slug)
                    self.assertEqual('region', region.get('role'), slug)
                    self.assertTrue(region['contains_table'], f'{slug}: region must contain a table')
                    labelledby = region.get('aria-labelledby', '').split()
                    self.assertTrue(labelledby, f'{slug}: table region needs aria-labelledby')
                    for reference in labelledby:
                        self.assertIn(reference, collector.ids, f'{slug}: missing #{reference}')
                        label = normalize_text(' '.join(collector.label_texts.get(reference, [])))
                        self.assertTrue(
                            label,
                            f'{slug}: #{reference} must be a visible heading or caption with text',
                        )

    def test_task5_source_required_links_and_conversion_routes(self):
        engineering_text, engineering = self.target('engineering')
        if engineering_text is None:
            return
        report_links = [
            anchor for anchor in engineering.anchors
            if anchor.get('text') == 'Request Sample Test Report'
        ]
        self.assertGreaterEqual(len(report_links), 2)
        for anchor in report_links:
            self.assertEqual('/request-a-quote', normalize_route(anchor.get('href', '')))

        expected_engineering_faq_routes = (
            '/about/factory',
            '/engineering/testing-quality',
            '/engineering/custom-rf-design',
            '/engineering/npi',
            '/engineering/manufacturing',
        )
        self.assertEqual(5, len(engineering.faq_links))
        engineering_faq_routes = {
            normalize_route(urljoin('/engineering/', href))
            for links in engineering.faq_links
            for href in links
            if href
        }
        self.assertEqual(
            set(expected_engineering_faq_routes),
            engineering_faq_routes,
            'engineering FAQ links must cover every related detail page',
        )

        base_text, base = self.target('base-station-rf')
        if base_text is None:
            return
        primary_ctas = [
            anchor for anchor in base.anchors
            if anchor.get('text') == 'Request Base-Station RFQ'
        ]
        self.assertEqual(2, len(primary_ctas))
        for anchor in primary_ctas:
            self.assertEqual('/request-a-quote', normalize_route(anchor.get('href', '')))

        pim_ctas = [
            anchor for anchor in base.anchors
            if anchor.get('text') == 'Ask About PIM Verification'
        ]
        self.assertEqual(3, len(pim_ctas))
        for anchor in pim_ctas:
            href = anchor.get('href', '')
            self.assertEqual('/request-a-quote', normalize_route(href))
            self.assertIn('topic=pim-verification', href)

        base_faq_routes = {
            normalize_route(urljoin('/products/base-station-rf/', href))
            for links in base.faq_links
            for href in links
            if href
        }
        for required_route in (
            '/engineering/testing-quality',
            '/solutions/5g-base-station',
            '/resources/rfq-guide',
        ):
            self.assertIn(required_route, base_faq_routes, 'base-station FAQ routing')

        enclosure_text, enclosures = self.target('precision-enclosures')
        if enclosure_text is None:
            return
        self.assertEqual(5, len(enclosures.faq_links))
        enclosure_faq_routes = {
            normalize_route(urljoin('/products/precision-enclosures/', href))
            for links in enclosures.faq_links
            for href in links
            if href
        }
        self.assertEqual(
            {'/request-a-quote', '/engineering/npi'},
            enclosure_faq_routes,
            'enclosure FAQ links must cover the RFQ and NPI resources',
        )

    def test_engineering_faq_answers_end_with_related_links(self):
        text, collector = self.target('engineering')
        if text is None:
            return
        self.assertEqual(5, len(collector.faq_tail_links))
        self.assertTrue(all(collector.faq_tail_links), 'each engineering answer must end with its link')
        allowed_routes = {
            '/about/factory',
            '/engineering/custom-rf-design',
            '/engineering/npi',
            '/engineering/testing-quality',
            '/engineering/manufacturing',
        }
        self.assertEqual(5, len(collector.faq_links))
        for index, links in enumerate(collector.faq_links):
            self.assertTrue(links, f'engineering FAQ {index + 1} needs a related link')
            last_route = normalize_route(urljoin('/engineering/', links[-1]))
            self.assertIn(last_route, allowed_routes, f'engineering FAQ {index + 1}')

    def test_engineering_verification_rows_link_to_test_details(self):
        text, collector = self.target('engineering')
        if text is None:
            return
        for method in (
            'VNA / S-parameters',
            'PIM',
            'Reliability',
            'Matrix-switch automation',
        ):
            with self.subTest(method=method):
                matches = [
                    anchor for anchor in collector.table_anchors
                    if anchor.get('text') == method
                ]
                self.assertEqual(1, len(matches), method)
                self.assertEqual(
                    '/engineering/testing-quality',
                    normalize_route(matches[0].get('href', '')),
                    method,
                )

    def test_precision_faqs_are_grouped_by_source_topics(self):
        text, collector = self.target('precision-enclosures')
        if text is None:
            return
        self.assertEqual(['Drawings', 'Performance', 'Production'], [
            group['heading'] for group in collector.faq_groups
        ])
        self.assertEqual([1, 2, 2], [group['count'] for group in collector.faq_groups])

    def test_task5_claim_boundaries_and_qualifiers(self):
        required_qualifiers = {
            'base-station-rf': (
                'not a universal N78 rating',
                'not as a list of stocked configurations or guaranteed specifications',
            ),
            'precision-enclosures': (
                'capability directions only',
                'not a fixed lead-time promise',
                'not ordinary cabinet tolerances or uniform enclosure guarantees',
            ),
            'engineering': (
                'not a product-performance certification',
                'not a lead-time commitment',
                'depending on topology and validation',
                'not a universal tolerance',
                'not a universal plating guarantee',
            ),
        }
        claim_qualifier_pairs = {
            'base-station-rf': (
                ('N78', 'not a universal N78 rating'),
                ('RFQ framework', 'not as a list of stocked configurations'),
            ),
            'precision-enclosures': (
                ('IP55', 'capability directions only'),
                ('±0.01 mm', 'not ordinary cabinet tolerances'),
                ('1 μm', 'not ordinary cabinet tolerances'),
                ('about two weeks', 'not a fixed lead-time promise'),
            ),
            'engineering': (
                ('ISO 9001', 'not a product-performance certification'),
                ('500,000', 'not a lead-time commitment'),
                ('110 GHz', 'depending on topology and validation'),
                ('±0.01 mm', 'not a universal tolerance'),
                ('1 μm', 'not a universal plating guarantee'),
            ),
        }
        for slug, qualifiers in required_qualifiers.items():
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                visible_text = normalize_text(' '.join(collector.text_parts))
                attribute_text = normalize_text(' '.join(collector.attribute_texts))
                schema_text = normalize_text(' '.join(
                    value
                    for block in collector.jsonld_blocks
                    for value in jsonld_strings(block)
                ))
                for source_name, source_text in (
                    ('visible', visible_text),
                    ('attributes', attribute_text),
                    ('schema', schema_text),
                ):
                    self.assertEqual(
                        [],
                        forbidden_claim_matches(source_text),
                        f'{slug}: forbidden claim in {source_name}',
                    )
                for qualifier in qualifiers:
                    self.assertIn(qualifier, visible_text, slug)
                for claim, qualifier in claim_qualifier_pairs[slug]:
                    self.assert_qualifier_near_claim(
                        visible_text, claim, qualifier, slug
                    )

    def assert_qualifier_near_claim(self, text, claim, qualifier, slug, window=400):
        lowered_qualifier = qualifier.lower()
        for match in re.finditer(re.escape(claim), text, re.IGNORECASE):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            if lowered_qualifier in text[start:end].lower():
                return
        self.fail(f'{slug}: qualifier {qualifier!r} is not near claim {claim!r}')

    def test_shared_table_scroll_and_focus_styles(self):
        css = SONNE_CSS.read_text(encoding='utf-8')
        declarations = css_declarations_for_selector(css, '.sn-table-wrap')
        self.assertEqual('100%', declarations.get('max-width'))
        self.assertEqual('auto', declarations.get('overflow-x'))
        focus = css_declarations_for_selector(css, '.sn-table-wrap:focus-visible')
        self.assertEqual('3px solid var(--sn-cyan-dark)', focus.get('outline'))

    def test_contact_required_markers_are_distinct_from_labels(self):
        css = (WEBSITE / 'contact.html').read_text(encoding='utf-8')
        declarations = css_declarations_for_selector(
            css,
            '.sn-contact .sn-contact__form .sn-contact__required-label',
        )
        self.assertEqual('uppercase', declarations.get('text-transform'))
        self.assertEqual('var(--sn-cyan-dark)', declarations.get('color'))

    def test_rfq_guide_templates_do_not_force_mobile_overflow(self):
        css = (WEBSITE / 'rfq-guide.html').read_text(encoding='utf-8')
        templates = css_declarations_for_selector(
            css, '.sn-rfq-guide .sn-rfq-guide__templates'
        )
        self.assertEqual(
            'minmax(0, 1fr)', templates.get('grid-template-columns')
        )
        template = css_declarations_for_selector(
            css, '.sn-rfq-guide .sn-rfq-guide__template'
        )
        self.assertEqual('0', template.get('min-width'))

    def test_faq_answers_remain_visible_in_print(self):
        for slug, selector in (
            (
                'engineering',
                '.sn-engineering .sn-engineering__faq details::details-content',
            ),
            (
                'base-station-rf',
                '.sn-base-station .sn-base-station__faq details::details-content',
            ),
        ):
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                self.assertEqual(1, len(collector.styles))
                print_block = css_media_block(collector.styles[0], 'print')
                self.assertTrue(print_block, f'{slug}: print rules must be inside @media print')
                declarations = css_declarations_for_selector(print_block, selector)
                self.assertEqual(
                    'visible !important',
                    declarations.get('content-visibility'),
                )
                fallback_selector = selector.replace(
                    'details::details-content', 'details:not([open]) > p'
                )
                fallback = css_declarations_for_selector(print_block, fallback_selector)
                self.assertEqual('block !important', fallback.get('display'))
                self.assertEqual('block !important', declarations.get('display'))

    def test_waveguide_hero_links_meet_touch_target(self):
        text, collector = self.target('waveguide-components')
        if text is None:
            return
        self.assertEqual(1, len(collector.styles))
        declarations = css_declarations_for_selector(
            collector.styles[0],
            '.sn-waveguide .sn-waveguide__hero-paths a',
        )
        self.assertEqual('inline-flex', declarations.get('display'))
        self.assertEqual('center', declarations.get('align-items'))
        self.assertEqual('44px', declarations.get('min-height'))

    def test_route_cards_share_one_border_language(self):
        text, collector = self.target('products')
        if text is None:
            return
        self.assertNotIn('sn-products__route-card--custom', text)
        self.assertEqual(2, text.count('class="sn-products__route-card"'))
        self.assertEqual(1, len(collector.styles))
        card = css_declarations_for_selector(
            collector.styles[0], '.sn-products .sn-products__route-card'
        )
        self.assertEqual('1px solid var(--sn-line)', card.get('border'))
        self.assertNotIn('border-top-color', card)

    def test_product_hero_plates_run_flush_inside_dark_frames(self):
        text, collector = self.target('rf-combiners')
        if text is not None:
            self.assertEqual(1, len(collector.styles))
            media = css_declarations_for_selector(
                collector.styles[0],
                '.sn-combiners .sn-combiners__hero-media .sn-hero-plate__media',
            )
            self.assertEqual('0', media.get('padding'))
            self.assertEqual('var(--sn-white)', media.get('background'))
            image = css_declarations_for_selector(
                collector.styles[0],
                '.sn-combiners .sn-combiners__hero-media img',
            )
            self.assertEqual('16 / 9', image.get('aspect-ratio'))

        for slug, prefix in (
            ('rf-microwave-filters', 'sn-filters'),
            ('waveguide-components', 'sn-waveguide'),
        ):
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                self.assertEqual(1, len(collector.styles))
                base_css = css_without_media_queries(collector.styles[0])
                media_grid = css_declarations_for_selector(
                    base_css,
                    f'.{prefix} .{prefix}__hero-media',
                )
                self.assertEqual(
                    'repeat(2, minmax(0, 1fr))', media_grid.get('grid-template-columns')
                )
                self.assertEqual('14px', media_grid.get('gap'))
                self.assertEqual('start', media_grid.get('align-items'))
                plate_media = css_declarations_for_selector(
                    collector.styles[0],
                    f'.{prefix} .{prefix}__hero-media .sn-hero-plate__media',
                )
                self.assertEqual('0', plate_media.get('padding'))
                self.assertEqual('var(--sn-white)', plate_media.get('background'))
                plate_image = css_declarations_for_selector(
                    collector.styles[0],
                    f'.{prefix} .{prefix}__hero-media .sn-hero-plate img',
                )
                self.assertEqual('1', plate_image.get('aspect-ratio'))

    def test_shared_hero_plates_run_flush_without_mats(self):
        css = SONNE_CSS.read_text(encoding='utf-8')
        media = css_declarations_for_selector(css, '.sn-hero-plate__media')
        self.assertEqual('0', media.get('padding'))
        image = css_declarations_for_selector(css, '.sn-hero-plate img')
        self.assertEqual('cover', image.get('object-fit'))
        for slug, selector in (
            ('base-station-rf', '.sn-base-station .sn-base-station__hero-media .sn-hero-plate__media'),
            ('precision-enclosures', '.sn-enclosures .sn-enclosures__hero-media .sn-hero-plate__media'),
            ('products', '.sn-products .sn-products__hero-media .sn-hero-plate__media'),
        ):
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                self.assertEqual(1, len(collector.styles))
                self.assertNotIn('padding', css_declarations_for_selector(collector.styles[0], selector))

    def test_combiner_scenario_images_use_equal_evidence_cards(self):
        text, collector = self.target('rf-combiners')
        if text is None:
            return
        self.assertEqual(1, len(collector.styles))
        figure = css_declarations_for_selector(
            collector.styles[0],
            '.sn-combiners .sn-combiners__scenario-media figure',
        )
        self.assertEqual('relative', figure.get('position'))
        self.assertEqual('flex', figure.get('display'))
        self.assertEqual('column', figure.get('flex-direction'))
        self.assertEqual('0', figure.get('margin-bottom'))
        self.assertEqual('hidden', figure.get('overflow'))
        self.assertEqual('var(--sn-border)', figure.get('border'))
        frame = css_declarations_for_selector(
            collector.styles[0],
            '.sn-combiners .sn-combiners__scenario-frame',
        )
        self.assertNotIn('padding', frame)
        self.assertEqual('var(--sn-white)', frame.get('background'))
        self.assertNotIn('border', frame)
        image = css_declarations_for_selector(
            collector.styles[0],
            '.sn-combiners .sn-combiners__scenario-media img',
        )
        self.assertEqual('1024 / 571', image.get('aspect-ratio'))
        self.assertEqual('cover', image.get('object-fit'))
        self.assertEqual('inset(1px)', image.get('clip-path'))
        self.assertNotIn('padding', image)
        caption = css_declarations_for_selector(
            collector.styles[0],
            '.sn-combiners .sn-combiners__scenario-media figcaption',
        )
        self.assertEqual('absolute', caption.get('position'))
        self.assertEqual('0', caption.get('right'))
        self.assertEqual('0', caption.get('bottom'))
        self.assertEqual('0', caption.get('left'))
        self.assertEqual('0', caption.get('margin'))
        self.assertEqual('9px 12px', caption.get('padding'))
        self.assertEqual('rgba(5, 16, 27, .82)', caption.get('background'))
        self.assertEqual(2, text.count('class="sn-combiners__scenario-frame"'))
        self.assertEqual(
            2, text.count('<div class="sn-combiners__scenario-frame"><img'),
        )

    def test_all_page_figcaptions_are_image_bottom_overlay_bars(self):
        exempt = {
            'home.html',  # product-card tag bars, not descriptive captions
            'about-us.html',
            'contact-us.html',
            'blog.html',
        }
        checked_pages = 0
        checked_captions = 0
        for path in sorted(WEBSITE.glob('*.html')):
            if path.name in exempt:
                continue
            text = path.read_text(encoding='utf-8')
            if '<figcaption' not in text:
                continue
            checked_pages += 1
            checked_captions += text.count('<figcaption')
            collector = collect(text)
            css = collector.styles[0]
            wrapper_match = re.search(r'<div class="(sn-[a-z0-9-]+)', text)
            self.assertIsNotNone(wrapper_match, path.name)
            wrapper = wrapper_match.group(1)
            for selector, body in iter_css_rules(css):
                if 'figcaption' not in selector:
                    continue
                declarations = {}
                for declaration in body.split(';'):
                    name, separator, value = declaration.partition(':')
                    if separator:
                        declarations[name.strip()] = value.strip()
                with self.subTest(page=path.name, selector=selector):
                    self.assertEqual('absolute', declarations.get('position'))
                    self.assertEqual('0', declarations.get('right'))
                    self.assertEqual('0', declarations.get('bottom'))
                    self.assertEqual('0', declarations.get('left'))
                    self.assertEqual('0', declarations.get('margin'))
                    self.assertEqual('rgba(5, 16, 27, .82)', declarations.get('background'))
            figure = css_declarations_for_selector(css, f'.{wrapper} figure')
            self.assertEqual('relative', figure.get('position'), path.name)
            caption = css_declarations_for_selector(css, f'.{wrapper} figcaption')
            self.assertEqual('absolute', caption.get('position'), path.name)
            self.assertEqual('9px 12px', caption.get('padding'), path.name)
            self.assertEqual('rgba(5, 16, 27, .82)', caption.get('background'), path.name)
            self.assertEqual('rgba(252, 254, 255, .8)', caption.get('color'), path.name)
        self.assertGreaterEqual(checked_pages, 30)
        self.assertGreaterEqual(checked_captions, 130)

    def test_shared_hero_plate_caption_is_an_image_bottom_overlay_bar(self):
        css = SONNE_CSS.read_text(encoding='utf-8')
        plate = css_declarations_for_selector(css, '.sn-hero-plate')
        self.assertEqual('relative', plate.get('position'))
        self.assertEqual('hidden', plate.get('overflow'))
        caption = css_declarations_for_selector(css, '.sn-hero-plate figcaption')
        self.assertEqual('absolute', caption.get('position'))
        self.assertEqual('0', caption.get('right'))
        self.assertEqual('0', caption.get('bottom'))
        self.assertEqual('0', caption.get('left'))
        self.assertEqual('0', caption.get('margin'))
        self.assertEqual('9px 12px', caption.get('padding'))
        self.assertEqual('rgba(5, 16, 27, .82)', caption.get('background'))
        self.assertEqual('rgba(252, 254, 255, .8)', caption.get('color'))

    def test_multi_figure_rows_use_equal_framed_evidence_cards(self):
        cases = (
            (
                'rf-microwave-filters',
                '.sn-filters .sn-filters__evidence-grid',
                '.sn-filters .sn-filters__evidence-grid figure',
                '.sn-filters .sn-filters__evidence-grid figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'rf-microwave-filters',
                '.sn-filters .sn-filters__test-grid',
                '.sn-filters .sn-filters__test-grid figure',
                '.sn-filters .sn-filters__test-grid figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'rf-combiners',
                '.sn-combiners .sn-combiners__product-grid',
                '.sn-combiners .sn-combiners__product-grid figure',
                '.sn-combiners .sn-combiners__product-grid figcaption',
                'repeat(4, minmax(0, 1fr))',
            ),
            (
                'rf-combiners',
                '.sn-combiners .sn-combiners__scenario-media',
                '.sn-combiners .sn-combiners__scenario-media figure',
                '.sn-combiners .sn-combiners__scenario-media figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'rf-combiners',
                '.sn-combiners .sn-combiners__evidence-grid',
                '.sn-combiners .sn-combiners__evidence-grid figure',
                '.sn-combiners .sn-combiners__evidence-grid figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'waveguide-components',
                '.sn-waveguide .sn-waveguide__detail-grid',
                '.sn-waveguide .sn-waveguide__detail-grid figure',
                '.sn-waveguide .sn-waveguide__detail-grid figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'waveguide-components',
                '.sn-waveguide .sn-waveguide__application-media',
                '.sn-waveguide .sn-waveguide__application-media figure',
                '.sn-waveguide .sn-waveguide__application-media figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'waveguide-components',
                '.sn-waveguide .sn-waveguide__evidence-grid',
                '.sn-waveguide .sn-waveguide__evidence-grid figure',
                '.sn-waveguide .sn-waveguide__evidence-grid figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'base-station-rf',
                '.sn-base-station .sn-base-station__test-grid',
                '.sn-base-station .sn-base-station__test-grid figure',
                '.sn-base-station .sn-base-station__test-grid figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'engineering',
                '.sn-engineering .sn-engineering__factory-grid',
                '.sn-engineering .sn-engineering__factory-grid figure',
                '.sn-engineering .sn-engineering__factory-grid figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'precision-enclosures',
                '.sn-enclosures .sn-enclosures__manufacturing-grid',
                '.sn-enclosures .sn-enclosures__manufacturing-grid figure',
                '.sn-enclosures .sn-enclosures__manufacturing-grid figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'ibs-das-components',
                '.sn-ibs-das .sn-ibs-das__product-grid',
                '.sn-ibs-das .sn-ibs-das__product-grid figure',
                '.sn-ibs-das .sn-ibs-das__product-grid figcaption',
                'repeat(3, minmax(0, 1fr))',
            ),
            (
                'ibs-das-components',
                '.sn-ibs-das .sn-ibs-das__mapping-media',
                '.sn-ibs-das .sn-ibs-das__mapping-media figure',
                '.sn-ibs-das .sn-ibs-das__mapping-media figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'rf-accessories',
                '.sn-accessories .sn-accessories__pair',
                '.sn-accessories .sn-accessories__pair figure',
                '.sn-accessories .sn-accessories__pair figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'factory',
                '.sn-factory .sn-factory__grid',
                '.sn-factory .sn-factory__grid figure',
                '.sn-factory .sn-factory__grid figcaption',
                'repeat(4, minmax(0, 1fr))',
            ),
            (
                'factory',
                '.sn-factory .sn-factory__grid--three',
                '.sn-factory .sn-factory__grid--three figure',
                '.sn-factory .sn-factory__grid--three figcaption',
                'repeat(3, minmax(0, 1fr))',
            ),
            (
                '5g-base-station',
                '.sn-sol-5g .sn-sol-5g__evidence',
                '.sn-sol-5g .sn-sol-5g__evidence figure',
                '.sn-sol-5g .sn-sol-5g__evidence figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'das-ibs',
                '.sn-sol-das .sn-sol-das__evidence',
                '.sn-sol-das .sn-sol-das__evidence figure',
                '.sn-sol-das .sn-sol-das__evidence figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'fttx',
                '.sn-sol-fttx .sn-sol-fttx__shopfloor',
                '.sn-sol-fttx .sn-sol-fttx__shopfloor figure',
                '.sn-sol-fttx .sn-sol-fttx__shopfloor figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'satellite-earth-station',
                '.sn-sol-satellite .sn-sol-satellite__drawings',
                '.sn-sol-satellite .sn-sol-satellite__drawings figure',
                '.sn-sol-satellite .sn-sol-satellite__drawings figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'solutions',
                '.sn-solutions .sn-solutions__evidence',
                '.sn-solutions .sn-solutions__evidence figure',
                '.sn-solutions .sn-solutions__evidence figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
            (
                'microwave-backhaul',
                '.sn-sol-backhaul .sn-sol-backhaul__products',
                '.sn-sol-backhaul .sn-sol-backhaul__products figure',
                '.sn-sol-backhaul .sn-sol-backhaul__products figcaption',
                'repeat(2, minmax(0, 1fr))',
            ),
        )
        for slug, grid_selector, figure_selector, caption_selector, columns in cases:
            with self.subTest(slug=slug, grid=grid_selector):
                text, collector = self.target(slug)
                if text is None:
                    continue
                self.assertEqual(1, len(collector.styles))
                base_css = css_without_media_queries(collector.styles[0])
                grid = css_declarations_for_selector(base_css, grid_selector)
                self.assertEqual(columns, grid.get('grid-template-columns'))
                figure = css_declarations_for_selector(base_css, figure_selector)
                self.assertEqual('relative', figure.get('position'))
                self.assertEqual('flex', figure.get('display'))
                self.assertEqual('column', figure.get('flex-direction'))
                self.assertEqual('0', figure.get('margin-bottom'))
                self.assertEqual('hidden', figure.get('overflow'))
                self.assertEqual('var(--sn-border)', figure.get('border'))
                self.assertEqual('var(--sn-white)', figure.get('background'))
                caption = css_declarations_for_selector(base_css, caption_selector)
                self.assertEqual('absolute', caption.get('position'))
                self.assertEqual('0', caption.get('right'))
                self.assertEqual('0', caption.get('bottom'))
                self.assertEqual('0', caption.get('left'))
                self.assertEqual('0', caption.get('margin'))
                self.assertEqual('9px 12px', caption.get('padding'))
                self.assertEqual(
                    'rgba(5, 16, 27, .82)', caption.get('background')
                )

    def test_stacked_evidence_groups_use_framed_cards(self):
        cases = (
            (
                'satellite-earth-station',
                '.sn-sol-satellite .sn-sol-satellite__evidence',
                '.sn-sol-satellite .sn-sol-satellite__evidence figure',
                '.sn-sol-satellite .sn-sol-satellite__evidence figcaption',
                'minmax(0, .8fr) minmax(0, 1.2fr)',
            ),
            (
                'microwave-backhaul',
                '.sn-sol-backhaul .sn-sol-backhaul__manufacturing',
                '.sn-sol-backhaul .sn-sol-backhaul__manufacturing figure',
                '.sn-sol-backhaul .sn-sol-backhaul__manufacturing figcaption',
                'minmax(0, 1.25fr) minmax(0, .75fr)',
            ),
        )
        for slug, grid_selector, figure_selector, caption_selector, columns in cases:
            with self.subTest(slug=slug, grid=grid_selector):
                text, collector = self.target(slug)
                if text is None:
                    continue
                self.assertEqual(1, len(collector.styles))
                base_css = css_without_media_queries(collector.styles[0])
                grid = css_declarations_for_selector(base_css, grid_selector)
                self.assertEqual(columns, grid.get('grid-template-columns'))
                figure = css_declarations_for_selector(base_css, figure_selector)
                self.assertEqual('relative', figure.get('position'))
                self.assertEqual('flex', figure.get('display'))
                self.assertEqual('column', figure.get('flex-direction'))
                self.assertEqual('0', figure.get('margin-bottom'))
                self.assertEqual('hidden', figure.get('overflow'))
                self.assertEqual('var(--sn-border)', figure.get('border'))
                self.assertEqual('var(--sn-white)', figure.get('background'))
                caption = css_declarations_for_selector(base_css, caption_selector)
                self.assertEqual('absolute', caption.get('position'))
                self.assertEqual('0', caption.get('bottom'))
                self.assertEqual('0', caption.get('margin'))
                self.assertEqual('9px 12px', caption.get('padding'))
                self.assertEqual(
                    'rgba(5, 16, 27, .82)', caption.get('background')
                )

        text, collector = self.target('satellite-earth-station')
        if text is not None:
            figures = css_declarations_for_selector(
                css_without_media_queries(collector.styles[0]),
                '.sn-sol-satellite .sn-sol-satellite__evidence img',
            )
            self.assertEqual('16 / 9', figures.get('aspect-ratio'))
            self.assertEqual('cover', figures.get('object-fit'))

        text, collector = self.target('microwave-backhaul')
        if text is not None:
            base_css = css_without_media_queries(collector.styles[0])
            main_image = css_declarations_for_selector(
                base_css,
                '.sn-sol-backhaul .sn-sol-backhaul__manufacturing-main img',
            )
            self.assertEqual('16 / 9', main_image.get('aspect-ratio'))
            side_image = css_declarations_for_selector(
                base_css,
                '.sn-sol-backhaul .sn-sol-backhaul__manufacturing-side img',
            )
            self.assertEqual('16 / 10', side_image.get('aspect-ratio'))
            self.assertEqual('cover', side_image.get('object-fit'))

    def test_backhaul_product_images_run_flush_in_their_cards(self):
        text, collector = self.target('microwave-backhaul')
        if text is None:
            return
        self.assertEqual(1, len(collector.styles))
        card = css_declarations_for_selector(
            collector.styles[0], '.sn-sol-backhaul .sn-sol-backhaul__products figure'
        )
        self.assertEqual('0', card.get('padding'))
        self.assertEqual('hidden', card.get('overflow'))
        self.assertEqual('relative', card.get('position'))
        image = css_declarations_for_selector(
            collector.styles[0], '.sn-sol-backhaul .sn-sol-backhaul__products img'
        )
        self.assertEqual('16 / 10', image.get('aspect-ratio'))
        self.assertEqual('cover', image.get('object-fit'))
        self.assertEqual('inset(1px)', image.get('clip-path'))
        self.assertNotIn('background', image)
        caption = css_declarations_for_selector(
            collector.styles[0],
            '.sn-sol-backhaul .sn-sol-backhaul__products figcaption',
        )
        self.assertEqual('0', caption.get('margin'))
        self.assertEqual('9px 12px', caption.get('padding'))
        self.assertEqual('absolute', caption.get('position'))
        self.assertEqual('rgba(5, 16, 27, .82)', caption.get('background'))

    def test_product_plates_clip_baked_catalog_borders(self):
        cases = (
            ('rf-combiners', '.sn-combiners .sn-combiners__product-grid img', 'inset(1px)'),
            (
                'waveguide-components',
                '.sn-waveguide .sn-waveguide__product-frame img',
                'inset(1px)',
            ),
            (
                'waveguide-components',
                '.sn-waveguide .sn-waveguide__detail-grid figure:last-child img',
                'inset(1px)',
            ),
            ('rf-accessories', '.sn-accessories .sn-accessories__pair img', 'inset(1px)'),
            ('rf-accessories', '.sn-accessories .sn-accessories__matching img', 'inset(1px)'),
            (
                'rf-accessories',
                '.sn-accessories .sn-accessories__catalog-figure img',
                'inset(2px calc(28.125% + 2px))',
            ),
            (
                'rf-accessories',
                '.sn-accessories .sn-accessories__triptych img',
                'inset(1px)',
            ),
            ('ibs-das-components', '.sn-ibs-das .sn-ibs-das__product-grid img', 'inset(1px)'),
            (
                'ibs-das-components',
                '.sn-ibs-das .sn-ibs-das__mapping-media figure:last-child img',
                'inset(2px calc(12.5% + 2px))',
            ),
            (
                'satellite-earth-station',
                '.sn-sol-satellite .sn-sol-satellite__waveguides img',
                'inset(1px)',
            ),
            ('das-ibs', '.sn-sol-das .sn-sol-das__components img', 'inset(1px)'),
        )
        for slug, selector, expected_clip in cases:
            with self.subTest(slug=slug, selector=selector):
                text, collector = self.target(slug)
                if text is None:
                    continue
                self.assertEqual(1, len(collector.styles))
                declarations = css_declarations_for_selector(
                    collector.styles[0], selector
                )
                self.assertEqual(expected_clip, declarations.get('clip-path'))
                self.assertIn(declarations.get('padding'), (None, '0'))
                self.assertIn(declarations.get('border'), (None, '0'))

        text, collector = self.target('rf-accessories')
        if text is not None:
            mobile = css_declarations_for_selector(
                collector.styles[0],
                '.sn-accessories .sn-accessories__triptych-tile img',
            )
            self.assertEqual('16 / 9', mobile.get('aspect-ratio'))
            self.assertEqual(
                'inset(2px calc(21.875% + 2px))', mobile.get('clip-path')
            )

        frames = (
            ('rf-combiners', 'sn-combiners__product-frame', 4),
            ('waveguide-components', 'sn-waveguide__product-frame', 4),
            ('waveguide-components', 'sn-waveguide__detail-frame', 1),
            ('ibs-das-components', 'sn-ibs-das__product-frame', 3),
            ('ibs-das-components', 'sn-ibs-das__mapping-frame', 1),
            ('rf-accessories', 'sn-accessories__plate', 4),
            ('rf-accessories', 'sn-accessories__triptych-tile', 3),
        )
        for slug, frame_class, count in frames:
            with self.subTest(slug=slug, frame=frame_class):
                text, _ = self.target(slug)
                if text is None:
                    continue
                wrapper_pattern = re.compile(
                    r'<div class="(?:[^"]*\s)?'
                    + re.escape(frame_class)
                    + r'(?:\s[^"]*)?"><img'
                )
                self.assertEqual(
                    count,
                    len(wrapper_pattern.findall(text)),
                    f'{slug}: every {frame_class} wrapper must hold its image',
                )

    def test_internal_routes_and_nonempty_hrefs(self):
        for slug, (page_id, route) in TARGETS.items():
            with self.subTest(slug=slug):
                text, collector = self.target(slug)
                if text is None:
                    continue
                base = route if route.endswith('/') else route + '/'
                for anchor in collector.anchors:
                    href_value = anchor.get('href')
                    self.assertIsNotNone(href_value, f'{slug}: anchor without href')
                    if href_value is None:
                        continue
                    href = href_value.strip()
                    self.assertNotEqual('', href, f'{slug}: empty href')
                    self.assertNotEqual('#', href, f'{slug}: placeholder href')
                    if not href or href == '#':
                        continue
                    parsed = urlsplit(href)
                    scheme = parsed.scheme.lower()
                    self.assertNotIn(scheme, {'javascript', 'data'}, f'{slug}: {href}')
                    is_http = scheme in {'http', 'https'} or (not scheme and parsed.netloc)
                    if is_http and (parsed.hostname or '').lower().rstrip('.') == 'rf-sonne.com':
                        self.assertIn(
                            normalize_route(href), VALID_ROUTES,
                            f'{slug}: unplanned same-site route {href}',
                        )
                        continue
                    if parsed.scheme or parsed.netloc:
                        continue
                    resolved = urljoin(base, href)
                    self.assertIn(normalize_route(resolved), VALID_ROUTES, f'{slug}: unplanned route {href}')

    def test_combiners_power_divider_depth_and_routing_links(self):
        text, collector = self.target('rf-combiners')
        if text is None:
            return
        self.assertIn('Wilkinson and Reactive Power Divider Topologies', text)
        self.assertIn('Wilkinson power divider', text)
        self.assertIn('reactive power divider', text)
        self.assertNotIn('3dB hybrid coupler', text)
        self.assertIn('/products/waveguide-components/', text)
        self.assertIn('/products/ibs-das-components/', text)
        self.assertIn(
            '/resources/insights/duplexer-vs-diplexer-combiner-guide/', text
        )
        self.assertIn('/resources/insights/wilkinson-power-divider-guide/', text)
        self.assertIn('/resources/insights/rf-diplexer-guide/', text)

    def test_filters_bandpass_depth_and_routing_links(self):
        text, collector = self.target('rf-microwave-filters')
        if text is None:
            return
        self.assertIn('Read the Bandpass Filter Response before Comparing Structures', text)
        self.assertIn('Bandpass and Cavity Filters', text)
        self.assertGreaterEqual(text.lower().count('bandpass'), 12)
        self.assertIn('What is a bandpass filter?', text)
        self.assertIn('How do I specify bandpass filter bandwidth and rejection?', text)
        self.assertIn('/resources/insights/cavity-vs-waveguide-filter-selection-guide/', text)
        self.assertIn('/resources/insights/rf-filter-rfq-preparation-guide/', text)
        self.assertIn('/resources/insights/rf-diplexer-guide/', text)

    def test_insights_inbound_links_from_product_pages(self):
        expectations = {
            'waveguide-components': ['/resources/insights/rf-diplexer-guide/'],
            'base-station-rf': ['/resources/insights/rf-diplexer-guide/'],
            'passive-microwave-components': [
                '/resources/insights/wilkinson-power-divider-guide/'
            ],
        }
        for slug, hrefs in expectations.items():
            text, collector = self.target(slug)
            if text is None:
                continue
            for href in hrefs:
                self.assertIn(href, text, f'{slug} should link to {href}')


class SchemaOwnershipTests(unittest.TestCase):
    def test_rank_math_filter_owns_site_and_page_entities(self):
        source = (ROOT / 'functions.php').read_text(encoding='utf-8')
        for marker in (
            "add_filter('rank_math/json_ld'",
            "add_filter('rank_math/json_ld', 'sonne_filter_rank_math_json_ld', 100)",
            "add_action('rank_math/head', 'sonne_rank_math_json_ld_buffer_start', 89)",
            'rank-math-schema',
            "is_singular('post')",
            "'en-US'",
            "'Organization'",
            "'Person'",
            "'Article'",
            'alternateName',
            'template-parts/data/site-contact.php',
            '#organization',
            "$is_graph = isset($data['@graph'])",
            'organization_added',
        ):
            self.assertIn(marker, source)

    def test_theme_templates_do_not_repeat_rank_math_entities(self):
        footer = (ROOT / 'template-parts' / 'footer.php').read_text(encoding='utf-8')
        self.assertNotIn('application/ld+json', footer)
        self.assertNotIn("'@type' => 'Organization'", footer)
        for name in ('single-post.php', 'home.php', 'category.php', 'archive.php'):
            source = (ROOT / name).read_text(encoding='utf-8')
            self.assertNotIn("'@type' => 'BlogPosting'", source, name)
            self.assertNotIn("'@type' => 'Blog'", source, name)
            self.assertNotIn("'@type' => 'CollectionPage'", source, name)
            self.assertIn('sonne_breadcrumb_schema(', source, name)

    def test_active_fragments_keep_only_product_faq_and_breadcrumb(self):
        pages = json.loads((ROOT / 'pages.json').read_text(encoding='utf-8'))
        slugs = sorted(
            page['slug'] for page in pages
            if (WEBSITE / f"{page['slug']}.html").is_file()
        )
        self.assertTrue(slugs)
        for slug in slugs:
            with self.subTest(slug=slug):
                text = (WEBSITE / f'{slug}.html').read_text(encoding='utf-8')
                collector = collect(text)
                self.assertTrue(collector.jsonld_blocks, slug)
                top_level = []
                for block in collector.jsonld_blocks:
                    try:
                        document = json.loads(block)
                    except json.JSONDecodeError as error:
                        self.fail(f'{slug}: invalid JSON-LD: {error}')
                    top_level.extend(iter_top_level_jsonld_objects(document))
                entity_types = [schema_types(item) for item in top_level]
                union = set().union(*entity_types)
                self.assertEqual(set(), union - FRAGMENT_SCHEMA_TYPES, slug)
                expected_breadcrumbs = 0 if slug == 'home' else 1
                self.assertEqual(
                    expected_breadcrumbs,
                    sum('BreadcrumbList' in types for types in entity_types),
                    f'{slug}: breadcrumb count',
                )
                self.assertLessEqual(
                    sum('Product' in types for types in entity_types), 1, slug
                )
                self.assertLessEqual(
                    sum('FAQPage' in types for types in entity_types), 1, slug
                )


SYSTEM_WRAPPERS = {
    'thank-you': 'sn-thank-you',
    'terms-of-service': 'sn-terms',
    'privacy-policy': 'sn-privacy',
    'sitemap': 'sn-sitemap',
}
SYSTEM_ROUTES = {'/thank-you', '/terms-of-service', '/privacy-policy', '/sitemap'}


class SystemPageTests(unittest.TestCase):
    maxDiff = None

    def test_system_pages_follow_the_sonne_shell(self):
        for slug, wrapper in SYSTEM_WRAPPERS.items():
            with self.subTest(slug=slug):
                path = WEBSITE / f'{slug}.html'
                self.assertTrue(path.is_file(), f'{slug}: missing fragment')
                if not path.is_file():
                    continue
                text = path.read_text(encoding='utf-8')
                collector = collect(text)
                self.assertTrue(text.lstrip().startswith('<!-- wp:html -->'), slug)
                self.assertNotRegex(text, r'<(?:html|body|main)(?:\s|>)', slug)
                self.assertNotRegex(text, r'\sstyle\s*=', slug)
                self.assertEqual(1, count_h1(text), slug)
                self.assertEqual([wrapper], collector.wrappers, slug)
                self.assertEqual(1, len(collector.styles), slug)
                selectors = [
                    selector
                    for rule in iter_css_selectors(collector.styles[0])
                    for selector in split_selector_list(rule)
                ]
                unscoped = [
                    selector for selector in selectors
                    if not selector_is_wrapper_rooted(selector, wrapper)
                ]
                self.assertEqual([], unscoped, f'{slug}: selectors escape .{wrapper}')
                visible = visible_copy(text).lower()
                for marker in LEGACY_MARKERS:
                    self.assertNotIn(marker, visible, f'{slug}: {marker}')
                self.assertEqual([], forbidden_claim_matches(visible), slug)
                for image in collector.images:
                    src = image.get('src', '').strip()
                    alt = image.get('alt')
                    self.assertTrue(alt and alt.strip(), f'{slug}: empty alt on {src}')
                    self.assertIn(src, VERIFIED_MEDIA_URLS, f'{slug}: unverified {src}')
                    self.assertIn(src, MEDIA_BY_URL, f'{slug}: missing manifest entry for {src}')
                    media = MEDIA_BY_URL[src]
                    self.assertEqual(media['alt'], alt, f'{slug}: manifest alt mismatch')
                    self.assertEqual(str(media['width']), image.get('width'), slug)
                    self.assertEqual(str(media['height']), image.get('height'), slug)
                allowed = VALID_ROUTES | SYSTEM_ROUTES
                for anchor in collector.anchors:
                    href = (anchor.get('href') or '').strip()
                    self.assertTrue(href, f'{slug}: empty href')
                    self.assertNotEqual('#', href, f'{slug}: placeholder href')
                    parsed = urlsplit(href)
                    self.assertNotIn(parsed.scheme.lower(), {'javascript', 'data'}, slug)
                    is_site = (
                        (parsed.scheme in {'http', 'https'} or not parsed.scheme and parsed.netloc)
                        and (parsed.hostname or '').lower().rstrip('.') == 'rf-sonne.com'
                    )
                    if is_site:
                        self.assertIn(normalize_route(href), allowed, f'{slug}: {href}')
                    elif not parsed.scheme and not parsed.netloc:
                        base = f'https://rf-sonne.com/{slug}/'
                        self.assertIn(
                            normalize_route(urljoin(base, href)),
                            allowed,
                            f'{slug}: unplanned route {href}',
                        )


class P3HarnessRegressionTests(unittest.TestCase):
    """Prove that the structural gate rejects the round-one review bypasses."""

    def run_page_check(self, method_name, html):
        case = P3PageTests(method_name)
        with patch.dict(TARGETS, {'home': ('page-01', '/')}, clear=True):
            with patch.object(case, 'target', return_value=(html, collect(html))):
                getattr(case, method_name)()

    def assert_wrapper_and_style_rejected(self, html):
        with self.assertRaises(AssertionError):
            self.run_page_check('test_exact_wrapper_and_one_scoped_style', html)

    def test_css_selector_branches_cannot_escape_the_wrapper(self):
        invalid_selectors = (
            '.sn-home + .outside',
            '.sn-home ~ .outside',
            'body .sn-home .title',
            ':not(.sn-home) .title',
            '[data-class=".sn-home"] .title',
            '.sn-home:has(+ .outside)',
            ':is(.sn-home, body) .title',
            ':where(.sn-home, .outside) .title',
            ':is(:where(.sn-home, body)) .title',
        )
        for selector in invalid_selectors:
            with self.subTest(selector=selector):
                html = f'<main class="sn-home"><style>{selector} {{ color: red; }}</style><h1>Title</h1></main>'
                self.assert_wrapper_and_style_rejected(html)

    def test_valid_wrapper_rooted_css_is_accepted(self):
        css = '''
            .sn-home { color: black; }
            .sn-home > .title, :is(.sn-home, .sn-home.theme) .title { color: blue; }
            @media (min-width: 40rem) {
                :where(.sn-home) .title, .sn-home .icon + .label { display: block; }
            }
        '''
        html = f'<main class="sn-home"><style>{css}</style><h1>Title</h1><p>Content</p></main>'
        self.run_page_check('test_exact_wrapper_and_one_scoped_style', html)

    def test_empty_wrapper_with_content_outside_is_rejected(self):
        html = '''<!-- wp:html -->
            <div class="sn-home"><style>.sn-home .title { color: red; }</style></div>
            <main><h1>Title</h1><p>Rendered outside the wrapper</p></main>
        '''
        self.assert_wrapper_and_style_rejected(html)

    def test_real_top_level_wrapper_with_content_is_accepted(self):
        html = '''<!-- wp:html -->
            <script type="application/ld+json">{}</script>
            <main class="sn-home">
                <style>.sn-home .title { color: black; }</style>
                <h1 class="title">Title</h1><p>Rendered inside the wrapper</p>
            </main>
        '''
        self.run_page_check('test_exact_wrapper_and_one_scoped_style', html)

    def test_absolute_and_protocol_relative_same_site_routes_are_checked(self):
        for href in ('https://rf-sonne.com/unplanned', '//rf-sonne.com/unplanned'):
            with self.subTest(href=href):
                html = f'<main class="sn-home"><a href="{href}">Unplanned</a></main>'
                with self.assertRaises(AssertionError):
                    self.run_page_check('test_internal_routes_and_nonempty_hrefs', html)

    def test_valid_same_site_and_exempt_links_are_accepted(self):
        valid_hrefs = (
            'https://rf-sonne.com/products',
            'http://rf-sonne.com/products/',
            '//rf-sonne.com/engineering?ref=nav#top',
            'https://rf-sonne.com',
            'https://example.com/unplanned',
            '//example.com/unplanned',
            'mailto:engineering@example.com',
            'tel:+1-555-0100',
        )
        anchors = ''.join(f'<a href="{href}">Link</a>' for href in valid_hrefs)
        html = f'<main class="sn-home">{anchors}</main>'
        self.run_page_check('test_internal_routes_and_nonempty_hrefs', html)

    def test_nested_main_landmark_is_rejected(self):
        h1 = expected_h1('page-01')
        html = f'<main class="sn-home"><h1>{h1}</h1><p>Content</p></main>'
        with self.assertRaises(AssertionError):
            self.run_page_check('test_fragment_shell_exact_h1_and_forbidden_markers', html)

    def test_style_and_script_text_cannot_leak_into_content_buffers(self):
        html = '''<main class="sn-home"><h2 id="label">Visible heading<style>
            .x::after { content: "hidden-label"; }
        </style></h2>
        <a href="/">Visible link<style>.x { content: "hidden-link"; }</style></a>
        <details><summary>Question</summary><p>Visible answer<style>
            .x { content: "hidden-answer"; }</style></p></details>
        <script type="application/ld+json">{"@type":"Thing","name":"Schema value"}</script>
        </main>'''
        collector = collect(html)
        self.assertIn('Visible heading', collector.label_texts['label'])
        self.assertNotIn('hidden-label', ' '.join(collector.label_texts['label']))
        self.assertEqual('Visible link', collector.anchors[0]['text'])
        self.assertNotIn('hidden-link', collector.anchors[0]['text'])
        self.assertIn('Visible answer', collector.faqs[0][1])
        self.assertNotIn('hidden-answer', collector.faqs[0][1])
        self.assertNotIn('Schema value', ' '.join(collector.text_parts))

    def test_claim_guard_rejects_unqualified_positive_claims(self):
        forbidden = (
            'Salt-spray tested for 500 hours and EMC compliant for every enclosure.',
            'IP68 certified for all outdoor cabinets.',
            'Guaranteed N78 performance for every site.',
            'IP68 certified housing',
        )
        for text in forbidden:
            with self.subTest(text=text):
                self.assertTrue(forbidden_claim_matches(text), text)

        allowed = (
            'None is a blanket certification for every cabinet or housing.',
            'RoHS, REACH, salt-spray and EMC compliance are not claimed here.',
            'not as a list of stocked configurations or guaranteed specifications.',
            'not a product-performance certification.',
            'Does annual capacity guarantee a production lead time?',
            'not a universal plating guarantee',
        )
        for text in allowed:
            with self.subTest(text=text):
                self.assertEqual([], forbidden_claim_matches(text), text)

    def test_faq_tail_link_requires_answer_text_to_end_with_the_link(self):
        html = '''<main class="sn-home">
        <details open><summary><a href="/summary-link">Summary link</a></summary><p>Answer</p></details>
        <details><summary>Question</summary><p><a href="/tail">Tail.</a><img src="x.webp" alt=""></p></details>
        <details><summary>Question</summary><p>Answer <a href="/end">ends here.</a></p></details>
        </main>'''
        collector = collect(html)
        self.assertEqual([False, False, True], collector.faq_tail_links)

    def test_faq_group_survives_nested_divs(self):
        html = '''<main class="sn-home">
        <div class="sn-home__faq-group"><h3>Group A</h3>
          <div class="note">Note</div>
          <details><summary>Q1</summary><p>A1</p></details>
          <details><summary>Q2</summary><p>A2</p></details>
        </div>
        <div class="sn-home__faq-group"><h3>Group B</h3>
          <details><summary>Q3</summary><p>A3</p></details>
        </div>
        </main>'''
        collector = collect(html)
        self.assertEqual(
            [('Group A', 2), ('Group B', 1)],
            [(group['heading'], group['count']) for group in collector.faq_groups],
        )

    def test_table_anchor_scope_excludes_links_outside_named_regions(self):
        html = '''<main class="sn-home">
        <a href="/outside">Outside link</a>
        <div class="sn-table-wrap" tabindex="0" role="region" aria-labelledby="label">
          <table><tr><td><a href="/inside">Inside link</a></td></tr></table>
        </div>
        </main>'''
        collector = collect(html)
        self.assertEqual(
            ['/inside'],
            [anchor.get('href') for anchor in collector.table_anchors],
        )

    def test_jsonld_strings_traverses_string_arrays(self):
        block = '''{"@graph": [{
            "name": "alpha",
            "keywords": ["beta", {"nested": ["gamma", "delta"]}]
        }]}'''
        self.assertEqual(
            ['alpha', 'beta', 'gamma', 'delta'],
            list(jsonld_strings(block)),
        )

    def test_uploaded_image_without_manifest_entry_is_rejected(self):
        src = next(iter(VERIFIED_MEDIA_URLS))
        html = f'<main class="sn-home"><img src="{src}" alt="Registry image"></main>'
        with patch.dict(MEDIA_BY_URL, clear=True):
            with self.assertRaises(AssertionError):
                self.run_page_check('test_verified_media_urls_and_nonempty_alts', html)

    def test_table_region_names_require_visible_heading_or_caption_text(self):
        invalid_html = (
            '<main class="sn-home"><p id="label">Not a heading</p>'
            '<div class="sn-table-wrap" tabindex="0" role="region" aria-labelledby="label">'
            '<table><tr><td>Data</td></tr></table></div></main>',
            '<main class="sn-home"><h2 id="label"> </h2>'
            '<div class="sn-table-wrap" tabindex="0" role="region" aria-labelledby="label">'
            '<table><tr><td>Data</td></tr></table></div></main>',
            '<main class="sn-home"><h2 id="label">Selection inputs</h2>'
            '<div class="sn-table-wrap" tabindex="0" role="region" aria-labelledby="label">'
            '<p>No table in this region</p></div></main>',
        )
        for html in invalid_html:
            with self.subTest(html=html):
                with self.assertRaises(AssertionError):
                    self.run_page_check('test_table_regions_are_keyboard_accessible', html)

        valid_html = '''<main class="sn-home"><h2 id="label">Selection inputs</h2>
            <div class="sn-table-wrap" tabindex="0" role="region" aria-labelledby="label">
            <table><tr><td>Data</td></tr></table></div></main>'''
        self.run_page_check('test_table_regions_are_keyboard_accessible', valid_html)


def expected_tdk(page_id):
    lines = SOURCE_BY_ID[page_id]['tdk'].splitlines()
    return {
        'title': lines[lines.index('SEO Title') + 1].strip(),
        'description': lines[lines.index('Meta Description') + 1].strip(),
    }


def load_preview_site():
    path = ROOT / 'preview_site.py'
    spec = importlib.util.spec_from_file_location('preview_site', path)
    if spec is None or spec.loader is None:
        raise AssertionError(f'cannot load {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RequestAQuoteTests(unittest.TestCase):
    maxDiff = None

    def read_fragment(self):
        self.assertTrue(
            RFQ_FRAGMENT.is_file(),
            f'missing RFQ fragment: {RFQ_FRAGMENT}',
        )
        return RFQ_FRAGMENT.read_text(encoding='utf-8') if RFQ_FRAGMENT.is_file() else ''

    def read_form(self):
        self.assertTrue(
            RFQ_FORM.is_file(),
            f'missing RFQ CF7 template: {RFQ_FORM}',
        )
        return RFQ_FORM.read_text(encoding='utf-8') if RFQ_FORM.is_file() else ''

    def read_mail(self):
        self.assertTrue(
            RFQ_MAIL.is_file(),
            f'missing RFQ mail contract: {RFQ_MAIL}',
        )
        return load_json(RFQ_MAIL) if RFQ_MAIL.is_file() else {}

    def form_tags(self, source=None):
        return parse_cf7_tags(self.read_form() if source is None else source)

    def tags_by_name(self, tags):
        return {tag['name']: tag for tag in tags if tag['name']}

    def group_source(self, form_source, group):
        match = re.search(
            r'<fieldset\b[^>]*data-rfq-product-group="'
            + re.escape(group)
            + r'"[^>]*>(.*?)</fieldset>',
            form_source,
            re.DOTALL,
        )
        self.assertIsNotNone(match, f'missing specification group: {group}')
        return match.group(1) if match else ''

    def test_fragment_shell_scope_and_single_h1(self):
        text = self.read_fragment()
        collector = collect(text)
        self.assertTrue(text.lstrip().startswith('<!-- wp:html -->'))
        self.assertIn('<!-- /wp:html -->', text)
        self.assertNotRegex(text, r'<(?:html|body|main)(?:\s|>)')
        self.assertNotRegex(text, r'\sstyle\s*=')
        self.assertNotRegex(text, r'\son[a-z]+\s*=')
        self.assertEqual([RFQ_H1], collector.h1s)
        self.assertEqual(['sn-rfq'], collector.wrappers)
        self.assertEqual(
            ['sn-rfq'],
            [item['class'] for item in collector.top_level_wrappers],
        )
        self.assertEqual(
            [True],
            [item['has_content'] for item in collector.top_level_wrappers],
        )
        self.assertFalse(collector.content_outside_wrapper)
        self.assertEqual(1, len(collector.styles))
        selectors = [
            selector
            for rule in iter_css_selectors(collector.styles[0])
            for selector in split_selector_list(rule)
        ]
        self.assertTrue(selectors)
        self.assertEqual(
            [],
            [
                selector for selector in selectors
                if not selector_is_wrapper_rooted(selector, 'sn-rfq')
            ],
        )
        self.assertEqual([], collector.images)
        self.assertEqual([], collector.media_urls)
        self.assertNotIn('url(', collector.styles[0])
        for marker in LEGACY_MARKERS:
            self.assertNotIn(marker, text.lower())
        for marker in RFQ_SENSITIVE_MARKERS:
            self.assertNotIn(marker, text)
        self.assertIn('mailto:info@rf-sonne.com', text)

    def test_seven_section_order_and_shortcode_placement(self):
        fragment = self.read_fragment()
        form_source = self.read_form()
        self.assertEqual(list(RFQ_H2S[:4]), collect(form_source).h2s)
        self.assertEqual(list(RFQ_H2S[4:]), collect(fragment).h2s)
        self.assertEqual(4, collect(fragment).section_count)

        form_h2_ids = re.findall(r'<h2\b[^>]*\bid="([^"]+)"', form_source)
        self.assertEqual(4, len(form_h2_ids))
        self.assertEqual(len(form_h2_ids), len(set(form_h2_ids)))

        shortcode = re.search(r'\[contact-form-7\b[^\]]*\]', fragment)
        self.assertIsNotNone(shortcode)
        if shortcode is None:
            return
        positions = (
            fragment.index('<h1'),
            shortcode.start(),
            fragment.index(RFQ_H2S[4]),
            fragment.index(RFQ_H2S[5]),
        )
        self.assertEqual(sorted(positions), list(positions))

        section = re.search(r'<section\b[^>]*\bid="rfq-form"[^>]*>', fragment)
        self.assertIsNotNone(section)
        if section is None:
            return
        self.assertIn('aria-labelledby="rfq-basics-title"', section.group(0))
        self.assertIn('id="rfq-basics-title"', form_source)
        self.assertIn('scroll-margin-top', fragment)

    def test_shortcode_targets_the_new_request_form_not_the_legacy_contact_form(self):
        fragment = self.read_fragment()
        match = re.search(
            r'\[contact-form-7\s+id="([^"]+)"\s+title="Request a Quote"\]',
            fragment,
        )
        self.assertIsNotNone(match)
        if match is None:
            return
        form_id = match.group(1)
        self.assertRegex(form_id, r'^[a-z0-9]{7}$')
        self.assertNotEqual('0332f27', form_id)

    def test_product_line_radio_uses_cf7_6_radio_tag_syntax(self):
        form_source = self.read_form()
        self.assertNotRegex(form_source, r'\[radio\*')
        self.assertRegex(
            form_source,
            r'\[radio\s+product-line\b[^\]]*"RF Filters"[^\]]*\]',
        )
        tag = self.tags_by_name(self.form_tags(form_source))['product-line']
        self.assertEqual('radio', tag['type'])
        self.assertTrue(tag['required'])

    def test_required_optional_and_project_basics_contract(self):
        form_source = self.read_form()
        tags = self.form_tags(form_source)
        by_name = self.tags_by_name(tags)

        required = {
            name for name, tag in by_name.items() if tag['required']
        }
        self.assertEqual(RFQ_REQUIRED_FIELDS, required)
        for name in RFQ_OPTIONAL_FIELDS:
            with self.subTest(field=name):
                self.assertIn(name, by_name)
                self.assertFalse(by_name[name]['required'])

        self.assertEqual('email', by_name['your-email']['type'])
        self.assertEqual('textarea', by_name['application']['type'])
        self.assertEqual('radio', by_name['product-line']['type'])
        self.assertEqual(list(RFQ_PRODUCT_LINES), by_name['product-line']['values'])
        self.assertEqual('select', by_name['project-stage']['type'])
        self.assertEqual(list(RFQ_PROJECT_STAGES), by_name['project-stage']['values'])
        self.assertIn('include_blank', by_name['project-stage']['flags'])
        self.assertEqual('checkbox', by_name['consent']['type'])
        consent_copy = ' '.join(by_name['consent']['values'])
        self.assertIn(
            'SONNE may use the information I submit to review this RFQ '
            'and contact me about this project.',
            consent_copy,
        )
        self.assertNotIn('NDA', consent_copy)

        self.assertIn('Application / requirement summary', form_source)
        self.assertIn('Required', form_source)
        self.assertGreaterEqual(form_source.count('sn-rfq__required'), 7)
        for name in (
            'your-name',
            'your-email',
            'your-company',
            'application',
            'project-stage',
            'your-phone',
            'country',
            'sample-quantity',
            'expected-volume',
            'target-date',
            'confidentiality-notes',
        ):
            with self.subTest(label=name):
                self.assertIn(f'for="{name}"', form_source)
        self.assertRegex(form_source, r'<legend[^>]*>[^<]*Product line')
        self.assertIn('use_label_element', by_name['consent']['flags'])
        self.assertIn(
            'use_label_element',
            by_name['confidentiality-discussion']['flags'],
        )
        self.assertIn('YYYY-MM-DD', by_name['target-date']['options'].get('placeholder', ''))
        self.assertEqual(
            'select',
            by_name['file-1-purpose']['type'],
        )

    def test_contact_fields_declare_autocomplete_hints(self):
        form_source = self.read_form()
        by_name = self.tags_by_name(self.form_tags(form_source))
        expected = {
            'your-name': 'name',
            'your-email': 'email',
            'your-company': 'organization',
            'your-phone': 'tel',
            'country': 'country-name',
        }
        for name, token in expected.items():
            with self.subTest(field=name):
                self.assertEqual(token, by_name[name]['options'].get('autocomplete'))

    def test_summary_column_spans_the_full_form_height(self):
        fragment = self.read_fragment()
        self.assertRegex(
            fragment,
            r'\.sn-rfq \.sn-rfq__aside\s*\{[^}]*align-self:\s*stretch',
        )

    def test_summary_precedes_consent_and_submit_in_mobile_flow(self):
        form_source = self.read_form()
        self.assertLess(
            form_source.index('data-rfq-summary'),
            form_source.index('[submit "Submit RFQ"]'),
        )
        self.assertLess(
            form_source.index('<aside class="sn-rfq__aside"'),
            form_source.index('sn-rfq__submit-block'),
        )

    def test_product_line_choices_render_as_a_two_column_group(self):
        fragment = self.read_fragment()
        self.assertRegex(
            fragment,
            r'\.sn-rfq \.sn-rfq__choice-grid \.wpcf7-radio[^{]*\{'
            r'[^}]*grid-template-columns:\s*repeat\(2',
        )

    def test_product_line_spec_groups_allow_unknown_values(self):
        form_source = self.read_form()
        groups = re.findall(r'data-rfq-product-group="([^"]+)"', form_source)
        self.assertEqual(list(RFQ_SPEC_FIELDS), groups)
        self.assertIn('data-rfq-spec-groups', form_source)
        self.assertIn('Unknown values are acceptable', visible_copy(form_source))

        unknown_total = 0
        for group, expected_names in RFQ_SPEC_FIELDS.items():
            with self.subTest(group=group):
                inner = self.group_source(form_source, group)
                tags = self.form_tags(inner)
                if group == 'Other / Not Sure':
                    value_tags = [
                        tag for tag in tags if tag['type'] == 'textarea'
                    ]
                    self.assertEqual(['other-specifications'], [tag['name'] for tag in value_tags])
                    self.assertFalse(value_tags[0]['required'])
                    self.assertIn(
                        'sn-rfq__spec-value',
                        value_tags[0]['options'].get('class', ''),
                    )
                    self.assertFalse(any(tag['required'] for tag in tags))
                    continue

                value_tags = [tag for tag in tags if tag['type'] == 'text']
                self.assertEqual(list(expected_names), [tag['name'] for tag in value_tags])
                for tag in value_tags:
                    self.assertFalse(tag['required'], tag['name'])
                    self.assertTrue(tag['options'].get('placeholder'), tag['name'])
                    self.assertIn(
                        'sn-rfq__spec-value',
                        tag['options'].get('class', ''),
                        tag['name'],
                    )

                unknown_tags = [
                    tag for tag in tags
                    if tag['type'] == 'checkbox'
                    and tag['name'].endswith('-unknown')
                ]
                self.assertEqual(
                    [f'{name}-unknown' for name in expected_names],
                    [tag['name'] for tag in unknown_tags],
                )
                for tag in unknown_tags:
                    self.assertFalse(tag['required'], tag['name'])
                    self.assertEqual(['Unknown'], tag['values'])
                    self.assertIn('use_label_element', tag['flags'])
                unknown_total += len(unknown_tags)
                self.assertFalse(any(tag['required'] for tag in tags))
        self.assertEqual(26, unknown_total)

    def test_files_confidentiality_and_consent_boundary(self):
        form_source = self.read_form()
        by_name = self.tags_by_name(self.form_tags(form_source))
        for index in range(1, 4):
            with self.subTest(file=index):
                file_tag = by_name[f'file-{index}']
                self.assertEqual('file', file_tag['type'])
                self.assertFalse(file_tag['required'])
                self.assertEqual('10mb', file_tag['options'].get('limit'))
                self.assertEqual(
                    RFQ_FILE_TYPES,
                    file_tag['options'].get('filetypes'),
                )
                purpose = by_name[f'file-{index}-purpose']
                self.assertEqual('select', purpose['type'])
                self.assertEqual(list(RFQ_FILE_PURPOSES), purpose['values'])
                self.assertFalse(purpose['required'])
                revision = by_name[f'file-{index}-revision']
                self.assertEqual('text', revision['type'])
                self.assertFalse(revision['required'])

        self.assertEqual(
            'checkbox',
            by_name['confidentiality-discussion']['type'],
        )
        self.assertFalse(by_name['confidentiality-discussion']['required'])
        confidentiality_copy = ' '.join(
            by_name['confidentiality-discussion']['values']
        )
        self.assertIn('before sharing sensitive material', confidentiality_copy)
        self.assertEqual('textarea', by_name['confidentiality-notes']['type'])
        self.assertFalse(by_name['confidentiality-notes']['required'])
        self.assertNotIn('NDA', confidentiality_copy)

        copy = visible_copy(form_source)
        for token in (
            'PDF',
            'STEP/STP',
            'DXF',
            'XLSX/CSV',
            'ZIP',
            'PNG',
            'JPG',
            '10 MB per file',
        ):
            with self.subTest(token=token):
                self.assertIn(token, copy)
        self.assertIn('does not accept or define an NDA', copy)
        self.assertIn(
            'Do not upload sensitive files until a project-specific '
            'arrangement has been confirmed by both parties.',
            copy,
        )
        self.assertEqual(2, copy.lower().count('nda'))
        self.assertIn('not attached', copy.lower())

    def test_mail_configuration_routes_and_file_links(self):
        mail_config = self.read_mail()
        self.assertEqual({'mail', 'messages'}, set(mail_config))
        mail = mail_config['mail']
        messages = mail_config['messages']

        self.assertEqual('info@rf-sonne.com', mail['recipient'])
        self.assertEqual('', mail['attachments'])
        self.assertIn('Reply-To: [your-email]', mail['additional_headers'])
        self.assertIn('wordpress@rf-sonne.com', mail['sender'])
        self.assertTrue(mail['use_html'])
        self.assertTrue(mail['exclude_blank'])

        self.assertIn('RFQ', mail['subject'])
        self.assertIn('[product-line]', mail['subject'])
        self.assertIn('[your-company]', mail['subject'])

        tags = self.form_tags()
        defined = {
            tag['name'] for tag in tags
            if tag['name'] and tag['type'] != 'submit'
        }
        body_tags = set(re.findall(r'\[([a-z0-9_-]+)\]', mail['body'], re.IGNORECASE))
        special = {'_site_title', '_site_url', '_site_admin_email'}
        self.assertEqual(set(), defined - body_tags)
        self.assertEqual(set(), body_tags - special - defined)
        for index in range(1, 4):
            for suffix in ('', '-purpose', '-revision'):
                with self.subTest(file_tag=f'file-{index}{suffix}'):
                    self.assertIn(f'[file-{index}{suffix}]', mail['body'])
        for required in (
            '[your-name]',
            '[your-email]',
            '[your-company]',
            '[product-line]',
            '[application]',
            '[project-stage]',
            '[confidentiality-discussion]',
            '[confidentiality-notes]',
            '[consent]',
        ):
            with self.subTest(mail_tag=required):
                self.assertIn(required, mail['body'])
        self.assertIn('not attached', mail['body'].lower())
        self.assertIn('confidentiality', mail['body'].lower())

        self.assertIn('about 24 hours', messages['mail_sent_ok'])
        self.assertIn('not a formal quotation or delivery commitment', messages['mail_sent_ok'])
        self.assertNotRegex(json.dumps(messages, ensure_ascii=False), r'[\u4e00-\u9fff]')
        for marker in RFQ_SENSITIVE_MARKERS:
            self.assertNotIn(marker, json.dumps(mail_config))

    def test_five_faqs_match_source_and_keep_tail_links(self):
        fragment = self.read_fragment()
        blocks = re.findall(r'<details\b[^>]*>(.*?)</details>', fragment, re.DOTALL)
        self.assertEqual(5, len(blocks))
        self.assertIn(RFQ_H2S[4], fragment)

        faq_routes = set()
        for index, (block, expected) in enumerate(zip(blocks, RFQ_FAQS)):
            with self.subTest(faq=index + 1):
                summary = re.search(r'<summary\b[^>]*>(.*?)</summary>', block, re.DOTALL)
                answer = re.search(
                    r'<p class="sn-rfq__faq-text">(.*?)</p>',
                    block,
                    re.DOTALL,
                )
                self.assertIsNotNone(summary)
                self.assertIsNotNone(answer)
                if summary is None or answer is None:
                    continue
                self.assertEqual(expected[0], normalize_text(strip_tags(summary.group(1))))
                self.assertEqual(expected[1], normalize_text(strip_tags(answer.group(1))))
                tail = block[answer.end():]
                tail_links = re.findall(r'<a\b[^>]*href="([^"]+)"', tail)
                self.assertTrue(tail_links, f'FAQ {index + 1} needs a tail link')
                for href in tail_links:
                    route = normalize_route(href)
                    self.assertIn(route, VALID_ROUTES, href)
                    faq_routes.add(route)
        self.assertEqual(
            {'/resources/rfq-guide', '/contact', '/engineering/testing-quality'},
            faq_routes,
        )

    def test_jsonld_is_single_breadcrumb_without_page_or_faq(self):
        fragment = self.read_fragment()
        collector = collect(fragment)
        self.assertEqual(1, len(collector.jsonld_blocks))
        document = json.loads(collector.jsonld_blocks[0])
        top_level = list(iter_top_level_jsonld_objects(document))
        self.assertEqual(
            {'BreadcrumbList'},
            set().union(*(schema_types(item) for item in top_level)),
        )
        all_types = set().union(
            *(schema_types(item) for item in iter_jsonld_objects(document))
        )
        self.assertNotIn('FAQPage', all_types)
        self.assertNotIn('WebPage', all_types)

        breadcrumb = next(
            item for item in top_level if 'BreadcrumbList' in schema_types(item)
        )
        items = breadcrumb.get('itemListElement', [])
        self.assertEqual(2, len(items))
        self.assertEqual(
            [
                ('Home', 'https://rf-sonne.com/'),
                ('Request a Quote', RFQ_SITE_URL),
            ],
            [(item.get('name'), item.get('item')) for item in items],
        )
        self.assertEqual([1, 2], [item.get('position') for item in items])
        self.assertIn(RFQ_H1, fragment)
        self.assertEqual(1, count_h1(fragment))

    def test_internal_routes_self_anchor_and_contact_fallback(self):
        fragment = self.read_fragment()
        collector = collect(fragment)
        routes = set()
        for anchor in collector.anchors:
            href = anchor.get('href', '').strip()
            with self.subTest(href=href):
                self.assertTrue(href)
                self.assertFalse(href.lower().startswith('javascript:'))
                self.assertNotIn('/contact-us', href)
                if href.startswith('#'):
                    self.assertEqual('#rfq-form', href)
                    self.assertIn('id="rfq-form"', fragment)
                elif href.startswith('mailto:'):
                    self.assertIn('info@rf-sonne.com', href)
                    self.assertIn('subject=', href)
                else:
                    route = normalize_route(href)
                    self.assertIn(route, VALID_ROUTES, href)
                    self.assertNotEqual('/request-a-quote', route)
                    self.assertNotIn('tel:', href)
                    routes.add(route)
        for route in (
            '/resources/rfq-guide',
            '/products',
            '/contact',
            '/engineering/testing-quality',
        ):
            with self.subTest(route=route):
                self.assertIn(route, routes)

    def test_claim_boundaries_and_response_expectations(self):
        fragment = self.read_fragment()
        form_source = self.read_form()
        copy = f'{visible_copy(fragment)} {visible_copy(form_source)}'
        remaining = [
            match for match in forbidden_claim_matches(copy)
            if match.lower() != 'nda'
        ]
        self.assertEqual([], remaining)
        for pattern in (
            r'\b(?:accept|accepted|accepts|agreed|bound by)\b[^.]{0,40}\bNDA\b',
            r'\bNDA\b[^.]{0,40}\b(?:accepted|agreed|applies|included|covered)\b',
        ):
            with self.subTest(pattern=pattern):
                positive = []
                for match in re.finditer(pattern, copy, re.IGNORECASE):
                    context = copy[max(0, match.start() - 40):match.end()].lower()
                    if re.search(r'\b(?:not|no|never|cannot)\b', context):
                        continue
                    if copy[match.end():match.end() + 2].lstrip().startswith('?'):
                        continue
                    positive.append(match.group(0))
                self.assertEqual([], positive)
        self.assertNotIn('instant quote', copy.lower())
        self.assertNotIn('guaranteed price', copy.lower())
        self.assertIn('about 24 hours', copy)
        self.assertIn('not a formal quotation or delivery commitment', copy)
        self.assertIn('not a guaranteed firm quotation or delivery commitment', copy)
        self.assertIn('DC to 40 GHz', copy)
        self.assertIn('110 GHz', copy)
        self.assertIn('prototyping', copy)
        self.assertIn('two-week', copy)
        self.assertIn('not a blanket commitment', copy)
        self.assertIn('10 MB per file', copy)
        self.assertIn('Does not mean an NDA is accepted', copy)
        for marker in RFQ_SENSITIVE_MARKERS:
            self.assertNotIn(marker, form_source)

    def test_sticky_summary_process_and_success_path(self):
        fragment = self.read_fragment()
        form_source = self.read_form()
        form_copy = visible_copy(form_source)
        self.assertIn('data-rfq-summary', form_source)
        self.assertIn('sn-rfq__summary', form_source)
        self.assertIn('aria-live="polite"', form_source)
        for label in (
            'Name',
            'Company',
            'Product line',
            'Application',
            'Project stage',
            'Specifications',
            'Files',
            'Confidentiality',
        ):
            with self.subTest(summary_label=label):
                self.assertIn(label, form_source)
        process = (
            'Submitted',
            'Completeness Check',
            'Engineering Review',
            'Clarification or Next Step',
        )
        positions = [form_copy.index(step) for step in process]
        self.assertEqual(sorted(positions), positions)
        self.assertIn('[submit "Submit RFQ"]', form_source)
        self.assertIn('data-rfq-success', fragment)
        self.assertIn('sn-rfq__success', fragment)
        self.assertIn('role="status"', fragment)
        self.assertIn('hidden', fragment)
        self.assertIn('wpcf7submit', fragment)
        self.assertIn('wpcf7mailsent', fragment)
        self.assertIn('data-rfq-product-group', fragment)
        self.assertIn('product-line', fragment)
        self.assertEqual(2, fragment.count('<script'))
        self.assertIn('application/ld+json', fragment)
        self.assertNotRegex(fragment, r'\son[a-z]+\s*=')

    def test_rfq_inline_script_avoids_wordpress_escaped_ampersands(self):
        fragment = self.read_fragment()
        scripts = re.findall(
            r'<script\b(?![^>]*\btype="application/ld\+json")[^>]*>(.*?)</script>',
            fragment,
            re.DOTALL | re.IGNORECASE,
        )
        self.assertEqual(1, len(scripts))
        self.assertNotIn('&&', scripts[0])

    def test_form_accessibility_and_print_contract(self):
        fragment = self.read_fragment()
        form_source = self.read_form()
        tags = self.form_tags(form_source)
        for tag in tags:
            if tag['type'] in {'text', 'email', 'tel', 'textarea', 'select', 'file'}:
                with self.subTest(field=tag['name']):
                    self.assertIn(f'for="{tag["name"]}"', form_source)
            if tag['type'] in {'radio', 'checkbox'}:
                with self.subTest(choice=tag['name']):
                    self.assertIn('use_label_element', tag['flags'])
        self.assertRegex(form_source, r'<legend[^>]*>[^<]*Product line')
        self.assertIn('[submit "Submit RFQ"]', form_source)
        self.assertNotRegex(form_source, r'<(?:html|body|main|section|form|script|style)(?:\s|>)')
        self.assertNotRegex(form_source, r'\sstyle\s*=')
        self.assertEqual([], collect(form_source).images)
        style = collect(fragment).styles[0]
        self.assertRegex(style, r'min-height:\s*48px')
        self.assertRegex(style, r'min-height:\s*44px')
        self.assertIn(':focus-visible', style)
        self.assertIn('@media (prefers-reduced-motion: reduce)', style)
        self.assertIn('@media print', style)
        self.assertIn('details:not([open])', style)
        self.assertIn('@media (max-width: 900px)', style)
        summary_count = len(re.findall(r'<details\b', fragment))
        summary_tags = len(re.findall(r'<summary\b', fragment))
        self.assertEqual(summary_count, summary_tags)
        self.assertEqual(5, summary_count)
        for marker in (
            'band plan',
            'specifications',
            'drawings',
            'quantity',
            'project stage',
        ):
            with self.subTest(hero_overview=marker):
                self.assertIn(marker, visible_copy(fragment).lower())
        self.assertIn('1440', fragment + form_source)


class PreviewHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview = load_preview_site()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.tmp.name) / 'preview'
        cls.documents = cls.preview.build_preview(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_build_writes_one_noindex_document_per_target(self):
        expected_files = {
            'index.html',
            'request-a-quote.html',
            'thank-you.html',
            'terms-of-service.html',
            'privacy-policy.html',
            'sitemap.html',
        } | {f'{slug}.html' for slug in TARGETS if slug != 'home'} | NEW_PRODUCT_LINE_FILES
        self.assertEqual(38, len(expected_files))
        self.assertEqual(expected_files, {path.name for path in self.documents})
        self.assertEqual(38, len(self.documents))

        for page in self.preview.PREVIEW_PAGES:
            path = self.output / page.filename
            with self.subTest(page=page.slug):
                document = path.read_text(encoding='utf-8')
                self.assertIn(
                    '<meta name="robots" content="noindex, nofollow">',
                    document,
                )
                self.assertIn('<link rel="icon" href="data:,">', document)
                self.assertEqual(1, len(re.findall(r'<h1\b', document)))
                self.assertEqual(1, len(re.findall(r'<main\b', document)))
                self.assertEqual(1, document.count('</main>'))
                self.assertRegex(
                    document,
                    rf'<div class="{re.escape(WRAPPERS[page.slug])}(?:\s[^"]*)?">',
                )
                self.assertIn('site-header-shell', document)
                self.assertIn('site-mobile-nav', document)
                self.assertIn('class="site-footer"', document)
                self.assertIn('/assets/main.css', document)
                self.assertIn('/assets/sonne.css', document)
                self.assertIn('/assets/site-header.js', document)
                self.assertIn('href="/products/"', document)
                self.assertIn('href="/engineering/"', document)

    def test_titles_and_descriptions_come_from_the_source_table(self):
        system_tdk = {
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
        for page in self.preview.PREVIEW_PAGES:
            tdk = system_tdk.get(page.slug) or expected_tdk(page.source_id)
            document = (self.output / page.filename).read_text(encoding='utf-8')
            with self.subTest(page=page.slug):
                self.assertIn(
                    f'<title>{tdk["title"].replace("&", "&amp;")}</title>',
                    document,
                )
                self.assertIn(
                    'content="' + tdk['description'].replace('&', '&amp;') + '"',
                    document,
                )

    def test_route_resolution_serves_only_the_preview_targets(self):
        expected_routes = {
            '/': 'index.html',
            '/products': 'products.html',
            '/engineering': 'engineering.html',
            '/solutions': 'solutions.html',
            '/solutions/5g-base-station': '5g-base-station.html',
            '/engineering/manufacturing': 'manufacturing.html',
            '/resources/faq': 'faq.html',
            '/about/factory': 'factory.html',
            '/contact': 'contact.html',
            '/request-a-quote': 'request-a-quote.html',
            '/thank-you': 'thank-you.html',
            '/terms-of-service': 'terms-of-service.html',
            '/privacy-policy': 'privacy-policy.html',
            '/sitemap': 'sitemap.html',
            '/products/antenna-test-systems': 'antenna-test-systems.html',
            '/products/switch-matrices': 'switch-matrices.html',
            '/products/tr-modules': 'tr-modules.html',
            '/products/passive-microwave-components': 'passive-microwave-components.html',
            '/products/rf-front-ends': 'rf-front-ends.html',
        }
        self.assertEqual(38, len(self.preview.ROUTE_FILES))
        for route, filename in expected_routes.items():
            with self.subTest(route=route):
                self.assertEqual(
                    self.output / filename,
                    self.preview.resolve_request(route, self.output),
                )
                self.assertEqual(
                    self.output / filename,
                    self.preview.resolve_request(route + '/', self.output),
                )

        self.assertEqual(
            {'/resources', '/resources/insights'},
            set(self.preview.FUTURE_ROUTES),
        )
        self.assertIsNone(
            self.preview.resolve_request('/resources/insights/', self.output)
        )
        self.assertIsNone(self.preview.resolve_request('/', self.output / 'missing'))

    def test_contact_preview_renders_the_short_form(self):
        document = (self.output / 'contact.html').read_text(encoding='utf-8')
        self.assertNotIn('[contact-form-7', document)
        self.assertIn('data-contact-preview="true"', document)
        self.assertNotIn('data-rfq-preview', document)
        self.assertNotIn('name="product-line"', document)
        for name in ('your-name', 'your-company', 'your-email', 'contact-topic'):
            with self.subTest(field=name):
                self.assertIn(f'name="{name}"', document)
        for control_id in (
            'contact-name',
            'contact-company',
            'contact-email',
            'contact-topic',
            'contact-summary',
        ):
            with self.subTest(control=control_id):
                self.assertIn(f'id="{control_id}"', document)
                self.assertIn(f'for="{control_id}"', document)
        for topic in CONTACT_TOPICS:
            with self.subTest(topic=topic):
                self.assertIn(f'<option value="{topic}">', document)
        self.assertIn('<textarea', document)
        self.assertIn('<button type="submit">Send Message</button>', document)

    def test_request_a_quote_preview_renders_cf7_fields(self):
        document = (
            self.output / 'request-a-quote.html'
        ).read_text(encoding='utf-8')
        for heading in RFQ_H2S:
            with self.subTest(heading=heading):
                self.assertIn(heading, document)
        self.assertNotIn('[contact-form-7', document)
        self.assertNotIn('[text*', document)
        self.assertIn('data-rfq-preview="true"', document)
        self.assertEqual(
            5,
            len(re.findall(r'<input\b[^>]*name="product-line"', document)),
        )
        for names in RFQ_SPEC_FIELDS.values():
            for name in names:
                with self.subTest(spec_field=name):
                    self.assertIn(f'id="{name}"', document)
        self.assertEqual(
            26,
            len(
                re.findall(
                    r'<input\b[^>]*name="[a-z0-9-]+-unknown"',
                    document,
                )
            ),
        )
        for name in RFQ_REQUIRED_FIELDS:
            with self.subTest(field=name):
                if name in {'product-line', 'consent'}:
                    self.assertIn(f'name="{name}"', document)
                else:
                    self.assertIn(f'id="{name}"', document)
                    self.assertIn(f'for="{name}"', document)
        self.assertIn('type="email"', document)
        self.assertIn('type="file"', document)
        self.assertIn('wpcf7-form-control wpcf7-radio', document)
        self.assertIn(
            'accept=".pdf,.step,.stp,.dxf,.xlsx,.csv,.zip,.png,.jpg"',
            document,
        )
        self.assertIn('<button type="submit">Submit RFQ</button>', document)

    def test_route_resolution_cannot_reach_private_files(self):
        probes = (
            '/../w.secrets.json',
            '/%2e%2e/w.secrets.json',
            '/assets/../w.secrets.json',
            '/w.secrets.json',
            '/assets/nope.css',
            '/preview/index.html',
        )
        for probe in probes:
            with self.subTest(probe=probe):
                self.assertIsNone(
                    self.preview.resolve_request(probe, self.output)
                )

    def test_assets_are_copied_unchanged(self):
        asset_pairs = (
            (ROOT / 'main.css', self.output / 'assets' / 'main.css'),
            (ROOT / 'sonne.css', self.output / 'assets' / 'sonne.css'),
            (
                ROOT / 'assets' / 'site-header.js',
                self.output / 'assets' / 'site-header.js',
            ),
        )
        for source, copied in asset_pairs:
            with self.subTest(asset=source.name):
                self.assertEqual(
                    source.read_bytes(),
                    copied.read_bytes(),
                )

    def test_build_does_not_write_into_website(self):
        self.assertNotEqual(WEBSITE, self.preview.PREVIEW_DIR)
        for path in self.documents:
            self.assertFalse(WEBSITE in path.parents)


class WordPressTemplateTests(unittest.TestCase):
    def test_page_templates_wrap_content_in_main_landmark(self):
        for template in ('page.php', 'front-page.php'):
            with self.subTest(template=template):
                source = (ROOT / template).read_text(encoding='utf-8')
                self.assertEqual(1, source.count('<main id="main-content">'))
                self.assertEqual(1, source.count('</main>'))
                start = source.index('<main id="main-content">')
                end = source.index('</main>')
                self.assertIn('the_content()', source[start:end])
                self.assertNotIn('<h1', source.lower())


if __name__ == '__main__':
    unittest.main()
