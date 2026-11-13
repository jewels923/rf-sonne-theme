"""Contract: the HTML -> footer-script critical request chain is eliminated.

PSI (mobile) "Network dependency tree / Avoid chaining critical requests" showed
three tiny behaviour scripts chained after the document (critical path 618ms):
assets/site-header.js, assets/whatsapp-chat.js and GeneratePress menu.min.js.
All three printed in the footer WITHOUT defer/async, so the preload scanner only
discovered them at the end of the HTML stream -> serial HTML -> JS chain.

Fix: print all three in <head> with `defer`. defer makes the preload scanner
discover them at the start of the stream and fetch them low-priority in parallel
with the document (depth 1, not a chain), while execution still waits for parse
so the DOM is ready and behaviour is unchanged. Both child scripts already guard
on DOMContentLoaded, so they are defer-safe.

The only cross-origin reference on the page is https://wa.me (a click-through
navigation link, not a loaded subresource), so "no origins preconnected" is
correct and must NOT be "fixed" with a pointless preconnect hint.

Source-level contracts (no PHP render harness); behavioural gate is a live
browser check (mobile menu / WhatsApp / header) plus a Lighthouse re-run.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / 'functions.php'

HANDLES = ('child-theme-site-header', 'child-theme-whatsapp-chat', 'generate-menu')


def read(path):
    if not path.is_file():
        raise AssertionError('missing %s' % path)
    return path.read_text(encoding='utf-8')


def enqueue_footer_arg(source, handle):
    m = re.search(r"wp_enqueue_script\(\s*'%s'.*?,\s*(true|false)\s*\);" % re.escape(handle),
                  source, re.S)
    if not m:
        raise AssertionError('wp_enqueue_script for %s not found' % handle)
    return m.group(1)


class DeferFilterTests(unittest.TestCase):
    def setUp(self):
        self.functions = read(FUNCTIONS)

    def test_script_loader_tag_filter_registered(self):
        self.assertIn("add_filter('script_loader_tag'", self.functions)

    def test_filter_covers_all_three_behaviour_handles(self):
        for handle in HANDLES:
            self.assertIn("'%s'" % handle, self.functions)

    def test_filter_injects_defer_attribute(self):
        self.assertIn('defer', self.functions)
        # inserted before src so the tag becomes <script defer src=...>
        self.assertIn(' defer src=', self.functions)

    def test_filter_is_idempotent(self):
        # must not double-add defer if a tag already carries it
        self.assertIn("strpos($tag, ' defer')", self.functions)


class HeadPlacementTests(unittest.TestCase):
    def setUp(self):
        self.functions = read(FUNCTIONS)

    def test_child_scripts_enqueued_in_head(self):
        for handle in ('child-theme-site-header', 'child-theme-whatsapp-chat'):
            self.assertEqual('false', enqueue_footer_arg(self.functions, handle),
                             '%s must load in head (in_footer=false)' % handle)

    def test_generatepress_menu_moved_to_head(self):
        self.assertRegex(self.functions,
                         r"wp_script_add_data\(\s*'generate-menu'\s*,\s*'group'\s*,\s*0\s*\)")


class NoPointlessPreconnectTests(unittest.TestCase):
    def setUp(self):
        self.functions = read(FUNCTIONS)

    def test_no_preconnect_hint_for_navigation_only_origin(self):
        # wa.me is a click-through link, never a subresource; preconnecting is waste.
        self.assertNotIn('preconnect', self.functions)


class PhpSyntaxTests(unittest.TestCase):
    def test_functions_php_parses(self):
        try:
            from tree_sitter import Language, Parser
            import tree_sitter_php
        except ImportError as exc:
            self.skipTest('tree-sitter PHP parser unavailable: %s' % exc)
        parser = Parser(Language(tree_sitter_php.language_php()))
        tree = parser.parse(read(FUNCTIONS).encode('utf-8'))
        errors = []
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            if node.type == 'ERROR' or node.is_missing:
                errors.append('%s at line %d' % (node.type or 'missing', node.start_point[0] + 1))
            stack.extend(node.children)
        self.assertEqual([], errors)


if __name__ == '__main__':
    unittest.main()