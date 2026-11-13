"""Contract: render-blocking CSS is eliminated on rf-sonne.com.

PSI (mobile) flagged four render-blocking stylesheets. The fix splits CSS into:
  * a design-critical layer (sonne-fonts + sonne, plus sonne-insights on blog)
    inlined in <head> so first paint needs no blocking request, and
  * the heavy legacy layer (GeneratePress parent + main.css) loaded async via a
    style_loader_tag filter (rel=preload as=style + onload swap + noscript fallback).

Cascade order is preserved by DOM position: the async GP/main links print inside
wp_head, and the inline design layer prints AFTER them (GP < main < sonne <
insights). @font-face rules are order-independent.

These are source-level contracts (the project has no PHP render harness); the
behavioural gate is a live browser check for FOUC / intact design.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / 'functions.php'
HEADER = ROOT / 'header.php'


def read(path):
    if not path.is_file():
        raise AssertionError('missing %s' % path)
    return path.read_text(encoding='utf-8')


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


class AsyncLegacyLayerTests(unittest.TestCase):
    def setUp(self):
        self.functions = read(FUNCTIONS)

    def test_style_loader_tag_filter_registered(self):
        self.assertIn("add_filter('style_loader_tag'", self.functions)

    def test_filter_targets_gp_parent_and_main(self):
        self.assertIn("'generate-style'", self.functions)
        self.assertIn("'child-theme-main-css'", self.functions)

    def test_filter_emits_preload_onload_and_noscript(self):
        self.assertIn('rel="preload"', self.functions)
        self.assertIn('as="style"', self.functions)
        # onload swaps rel to stylesheet (single quotes are \' escaped in PHP source)
        self.assertIn('this.onload=null;this.rel=', self.functions)
        self.assertIn('stylesheet', self.functions)
        self.assertIn('<noscript>', self.functions)
        self.assertIn('rel="stylesheet"', self.functions)

    def test_main_still_enqueued_minified_with_version(self):
        # main.css stays an external (cached) stylesheet, just async now.
        self.assertIn("child_theme_css_path('main.css')", self.functions)
        self.assertIn('child_theme_asset_version($main_css)', self.functions)


class InlineDesignLayerTests(unittest.TestCase):
    def setUp(self):
        self.header = read(HEADER)
        self.functions = read(FUNCTIONS)

    def test_fonts_and_sonne_inlined_in_header(self):
        self.assertIn("child_theme_css_path('assets/css/sonne-fonts.css')", self.header)
        self.assertIn("child_theme_css_path('sonne.css')", self.header)
        self.assertIn('child_theme_inline_css', self.header)
        self.assertIn('<style', self.header)

    def test_insights_inlined_on_blog_only(self):
        self.assertIn("child_theme_css_path('assets/css/sonne-insights.css')", self.header)
        # same blog conditional as the former enqueue
        for cond in ('is_home()', 'is_category()', 'is_archive()', "is_singular('post')", "is_page('resources')", 'is_search()'):
            self.assertIn(cond, self.header)

    def test_inline_prints_after_wp_head_for_cascade(self):
        # async GP/main links live inside wp_head; inline design layer must follow
        # so sonne overrides main on equal-specificity rules.
        self.assertLess(self.header.index('echo $sonne_head'),
                        self.header.index("child_theme_css_path('sonne.css')"))

    def test_design_layer_handles_not_enqueued_blocking(self):
        for handle in ("'child-theme-fonts'", "'child-theme-sonne-css'", "'sonne-insights'"):
            self.assertNotIn(handle, self.functions)

    def test_inline_reads_minified_twin(self):
        # inline path goes through child_theme_css_path so the .min.css twin is used
        self.assertIn('function child_theme_css_path', self.functions)


class InlineFontUrlRebaseTests(unittest.TestCase):
    """Inlining moves relative url() resolution from the CSS file's directory to
    the document root, so @font-face src '../fonts/x.woff2' would 404 at
    /fonts/x.woff2. The inline helper must rebase explicitly-relative url() onto
    the stylesheet's own directory URI (leaving data:/absolute URLs untouched)."""

    def setUp(self):
        self.functions = read(FUNCTIONS)
        self.header = read(HEADER)
        self.fonts_css = read(ROOT / 'assets/css/sonne-fonts.css')

    def test_fonts_css_has_relative_font_urls_that_need_rebasing(self):
        self.assertIn("url('../fonts/", self.fonts_css)

    def test_inline_helper_rebases_relative_urls(self):
        self.assertIn('function child_theme_inline_css', self.functions)
        self.assertIn('preg_replace_callback', self.functions)
        self.assertIn('dirname(', self.functions)
        self.assertIn('get_stylesheet_directory_uri', self.functions)

    def test_header_inlines_through_rebasing_helper(self):
        self.assertIn('child_theme_inline_css(', self.header)
        # the raw, non-rebasing inline echo must be gone
        self.assertNotIn('file_get_contents($sonne_inline_abs)', self.header)


class PhpSyntaxTests(unittest.TestCase):
    def test_changed_php_files_parse(self):
        for path in (FUNCTIONS, HEADER):
            with self.subTest(path=path.name):
                try:
                    errors = php_syntax_errors(read(path))
                except ImportError as exc:
                    self.skipTest('tree-sitter PHP parser unavailable: %s' % exc)
                self.assertEqual([], errors)


if __name__ == '__main__':
    unittest.main()