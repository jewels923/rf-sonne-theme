import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'inc' / 'data' / 'insights.json'
CSS = ROOT / 'assets' / 'css' / 'sonne-insights.css'
SONNE_CSS = ROOT / 'sonne.css'
HUB = ROOT / 'website' / 'resources.html'
INSIGHTS = ROOT / 'inc' / 'insights.php'
FUNCTIONS = ROOT / 'functions.php'
HEADER = ROOT / 'header.php'
HOME = ROOT / 'home.php'
CATEGORY = ROOT / 'category.php'
SINGLE = ROOT / 'single-post.php'
ARCHIVE = ROOT / 'archive.php'
AUTHOR = ROOT / 'author.php'

TOPIC_SLUGS = (
    'rfq-preparation',
    'filter-selection',
    'waveguide-eband',
    'low-pim-combiners',
    'test-reports',
    'npi-manufacturing',
)
LEGACY = ('julong', 'wxkntest', 'sunglasses', 'sports eyewear', 'wa.me/8613450284642')
DEAD_LINKS = ('/resources/rfq-guide', '/resources/faq', '/resources/datasheets')
INSIGHTS_TITLE = 'RF & Microwave Engineering Insights | SONNE'
INSIGHTS_H1 = 'RF Engineering Guides for Buyers and Designers'
INSIGHTS_DESC = (
    'Practical RF guides: RFQ preparation, filter selection, waveguide and E-band '
    'engineering, low PIM design, test report reading and NPI for custom RF components.'
)
HUB_TITLE = 'RF Resources | Insights, RFQ Guide, FAQ & Datasheets | SONNE'
HUB_H1 = 'RF Engineering Resources and Buyer Tools'
HUB_DESC = (
    'RF engineering articles, RFQ checklists, strategic FAQ and datasheet downloads '
    'for custom RF, waveguide and enclosure projects.'
)


def php_syntax_errors(source):
    from tree_sitter import Language, Parser
    import tree_sitter_php

    parser = Parser(Language(tree_sitter_php.language_php()))
    tree = parser.parse(source.encode('utf-8'))
    errors = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == 'ERROR' or node.is_missing:
            errors.append('%s at line %d' % (node.type or 'missing', node.start_point[0] + 1))
        stack.extend(node.children)
    return errors


def read(path):
    if not path.is_file():
        raise AssertionError('missing %s' % path)
    return path.read_text(encoding='utf-8')


class PhpSyntaxTests(unittest.TestCase):
    def test_changed_php_files_parse(self):
        for path in (INSIGHTS, FUNCTIONS, HEADER, HOME, CATEGORY, SINGLE, ARCHIVE, AUTHOR):
            with self.subTest(path=path.name):
                try:
                    errors = php_syntax_errors(read(path))
                except ImportError as exc:
                    self.skipTest('tree-sitter PHP parser unavailable: %s' % exc)
                self.assertEqual([], errors)


class DataContractTests(unittest.TestCase):
    def config(self):
        return json.loads(read(CONFIG))

    def test_six_topics_in_order(self):
        topics = self.config()['topics']
        self.assertEqual(6, len(topics))
        self.assertEqual(TOPIC_SLUGS, tuple(t['slug'] for t in topics))
        for topic in topics:
            self.assertTrue(topic['name'])
            self.assertTrue(topic['description'].endswith('.'))
            self.assertEqual(topic['name'] + ' Guides | SONNE', topic['seo_title'])

    def test_page_and_hub_tdk_are_locked(self):
        config = self.config()
        self.assertEqual(INSIGHTS_TITLE, config['page']['title'])
        self.assertEqual(INSIGHTS_H1, config['page']['h1'])
        self.assertEqual(INSIGHTS_DESC, config['page']['description'])
        self.assertEqual('RF engineering guides', config['page']['focus_keyword'])
        self.assertEqual(HUB_TITLE, config['hub']['title'])
        self.assertEqual(HUB_H1, config['hub']['h1'])
        self.assertEqual(HUB_DESC, config['hub']['description'])
        self.assertEqual('RF resources', config['hub']['focus_keyword'])

    def test_five_strategy_faqs(self):
        faqs = self.config()['faqs']
        self.assertEqual(5, len(faqs))
        self.assertEqual('Which RF engineering guide should I read first?', faqs[0]['q'])
        self.assertEqual('Can an engineering guide replace a custom RFQ review?', faqs[-1]['q'])
        for faq in faqs:
            self.assertTrue(faq['a'].endswith('.'))


class HelperTests(unittest.TestCase):
    def source(self):
        return read(INSIGHTS)

    def test_required_helpers_exist(self):
        source = self.source()
        for name in (
            'sonne_insights_config',
            'sonne_insight_topics',
            'sonne_insights_url',
            'sonne_topic_url',
            'sonne_reading_time',
            'sonne_insight_excerpt',
            'sonne_insight_post_card',
            'sonne_insight_breadcrumbs',
            'sonne_breadcrumb_schema',
            'sonne_schema_json',
            'sonne_insight_content_anchors',
            'sonne_insight_toc_from_html',
            'sonne_insight_wrap_tables',
            'sonne_current_canonical_url',
        ):
            self.assertIn('function ' + name + '(', source)

    def test_output_is_escaped(self):
        source = self.source()
        for fn in ('esc_url(', 'esc_html(', 'esc_attr('):
            self.assertIn(fn, source)
        for bad in ('var_dump(', 'print_r(', 'error_log('):
            self.assertNotIn(bad, source)

    def test_author_archives_redirect(self):
        source = self.source()
        self.assertIn('is_author()', source)
        self.assertIn("wp_safe_redirect(home_url('/resources/insights/'), 301)", source)

    def test_guide_count_is_pluralised(self):
        source = self.source()
        self.assertIn('function sonne_guide_count(', source)
        self.assertIn("=== 1 ? 'guide' : 'guides'", source)
        for template in (HOME, CATEGORY):
            self.assertIn('sonne_guide_count(', read(template))

    def test_display_dates_stay_english(self):
        for path in (INSIGHTS, SINGLE):
            source = read(path)
            self.assertNotIn("get_the_date('M j, Y'", source)
            self.assertIn("get_post_time('M j, Y'", source)

    def test_content_filters_are_post_only(self):
        source = self.source()
        self.assertIn("is_singular('post')", source)
        self.assertIn("add_filter('the_content', 'sonne_insight_content_anchors'", source)
        self.assertIn("add_filter('the_content', 'sonne_insight_wrap_tables'", source)

    def test_image_sizes_are_registered(self):
        source = self.source()
        self.assertIn("add_image_size('sonne-insight-card', 800, 450, true)", source)
        self.assertIn("add_image_size('sonne-insight-wide', 1600, 900, true)", source)


class TemplateTests(unittest.TestCase):
    def test_each_template_uses_shared_chrome(self):
        for path in (HOME, CATEGORY, SINGLE, ARCHIVE):
            with self.subTest(path=path.name):
                source = read(path)
                self.assertIn('get_header()', source)
                self.assertIn("get_template_part('template-parts/header')", source)
                self.assertIn("get_template_part('template-parts/footer')", source)
                self.assertIn('get_footer()', source)
                self.assertIn('id="main-content"', source)

    def test_home_archive_contract(self):
        source = read(HOME)
        self.assertIn("$page['h1']", source)
        self.assertIn('sonne_insight_topics()', source)
        self.assertIn('sonne_insight_post_card(', source)
        self.assertIn('paginate_links(', source)
        self.assertIn("'@type' => 'Blog'", source)
        self.assertIn('sonne_breadcrumb_schema(', source)
        self.assertIn('The first SONNE guides are in preparation.', source)
        self.assertIn('Browse Guide Topics', source)

    def test_category_archive_contract(self):
        source = read(CATEGORY)
        self.assertIn('single_cat_title(', source)
        self.assertIn('category_description(', source)
        self.assertIn('sonne_insight_post_card(', source)
        self.assertIn('paginate_links(', source)
        self.assertIn("'@type' => 'CollectionPage'", source)
        self.assertIn('sonne_breadcrumb_schema(', source)
        self.assertIn('No guides in this topic yet.', source)

    def test_single_post_contract(self):
        source = read(SINGLE)
        self.assertIn('sonne_insight_toc_from_html(', source)
        self.assertIn('sonne_reading_time(', source)
        self.assertIn("'@type' => 'BlogPosting'", source)
        self.assertIn('sonne_breadcrumb_schema(', source)
        self.assertIn('SONNE Engineering', source)
        self.assertIn('<time datetime=', source)
        self.assertIn('Related Guides', source)
        self.assertIn('Request a Quote', source)
        self.assertNotIn('get_author_posts_url(', source)
        self.assertNotIn('author_link(', source)

    def test_author_template_redirects(self):
        source = read(AUTHOR)
        self.assertIn("wp_safe_redirect(home_url('/resources/insights/'), 301)", source)
        self.assertNotIn('get_header()', source)

    def test_archive_template_is_generic(self):
        source = read(ARCHIVE)
        self.assertIn('get_the_archive_title(', source)
        self.assertIn('sonne_insight_post_card(', source)
        self.assertIn('paginate_links(', source)


class ChromeTests(unittest.TestCase):
    def test_header_canonical_fallback_is_duplicate_safe(self):
        source = read(HEADER)
        self.assertNotIn("'/blog/'", source)
        self.assertIn('ob_start()', source)
        self.assertIn('wp_head()', source)
        self.assertIn('ob_get_clean()', source)
        self.assertIn('canonical', source)
        self.assertIn('sonne_current_canonical_url', source)

    def test_functions_loads_insights_module(self):
        source = read(FUNCTIONS)
        self.assertIn("inc/insights.php", source)
        self.assertIn("'/inc/insights.php'", source)
        self.assertIn('sonne-insights', source)
        self.assertIn("'/assets/css/sonne-insights.css'", source)


class CssTests(unittest.TestCase):
    def test_shared_cta_headings_stay_white(self):
        source = read(SONNE_CSS)
        self.assertRegex(source, r'\.sn-cta h2[^{]*\{[^}]*color:\s*var\(--sn-white\)')

    def test_uses_sonne_tokens_and_components(self):
        source = read(CSS)
        for selector in (
            '.sn-insights-hero',
            '.sn-topic-grid',
            '.sn-post-grid',
            '.sn-post-card',
            '.sn-empty',
            '.sn-pagination',
            '.sn-article-layout',
            '.sn-article__body',
            '.sn-toc',
            '.sn-resource-grid',
        ):
            self.assertIn(selector, source)
        self.assertIn('var(--sn-navy)', source)
        self.assertIn('var(--sn-cyan)', source)
        self.assertIn('@media (max-width: 1024px)', source)
        self.assertIn('@media (max-width: 768px)', source)
        self.assertIn('prefers-reduced-motion', source)
        self.assertNotIn('#1452FF', source)
        self.assertNotIn('#D7AE43', source)


class HubTests(unittest.TestCase):
    def source(self):
        return read(HUB)

    def test_hub_headings_and_copy(self):
        source = self.source()
        self.assertEqual(1, source.lower().count('<h1'))
        self.assertIn(HUB_H1, source)

    def test_hub_links_are_live(self):
        source = self.source()
        for href in ('/resources/insights/', '/request-a-quote/', '/engineering/', '/contact/'):
            self.assertIn('href="%s"' % href, source)

    def test_hub_schema(self):
        source = self.source()
        self.assertIn('"@type": "CollectionPage"', source)
        self.assertIn('"@type": "BreadcrumbList"', source)


class SafetyTests(unittest.TestCase):
    FILES = (CONFIG, INSIGHTS, FUNCTIONS, HEADER, HOME, CATEGORY, SINGLE, ARCHIVE, AUTHOR, HUB, CSS)

    def test_no_legacy_or_dead_links(self):
        for path in self.FILES:
            source = read(path).lower()
            with self.subTest(path=path.name):
                for marker in LEGACY:
                    self.assertNotIn(marker.lower(), source)
                for link in DEAD_LINKS:
                    self.assertNotIn(link.lower(), source)

    def test_no_credentials(self):
        for path in self.FILES:
            source = read(path)
            with self.subTest(path=path.name):
                for marker in ('w.secrets', 'app_password', 'sync_auth_token', 'Authorization: Basic'):
                    self.assertNotIn(marker, source)


if __name__ == '__main__':
    unittest.main()
