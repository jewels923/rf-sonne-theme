"""Contract: verify-live-home.py must load blog_setup from a path that exists.

The helper used to reference ROOT/'bak'/'qa'/'blog_setup.py'. blog_setup.py was
relocated to tools/qa/, so the stale 'bak' reference made the script crash on
import (spec_from_file_location -> FileNotFoundError) before any verification ran.

verify-live-home.py executes live network calls at module scope, so it cannot be
imported in a test. This is a source-level contract: parse the script, resolve the
path expression passed to spec_from_file_location('blog_setup', ...), and assert it
points at a real file. No eval, no network.
"""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools' / 'verify-live-home.py'
CANONICAL = ROOT / 'tools' / 'qa' / 'blog_setup.py'


def _resolve_path_expr(node):
    """Resolve a `ROOT / 'a' / 'b' / 'x.py'` expression without eval."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id == 'ROOT':
        return ROOT
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _resolve_path_expr(node.left) / _resolve_path_expr(node.right)
    raise AssertionError('unexpected path expression node: %s' % ast.dump(node))


def referenced_blog_setup_path():
    tree = ast.parse(SCRIPT.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', '')
        if name != 'spec_from_file_location' or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and first.value == 'blog_setup' and len(node.args) >= 2:
            return Path(_resolve_path_expr(node.args[1]))
    raise AssertionError("no spec_from_file_location('blog_setup', ...) call found in %s" % SCRIPT)


class VerifyLiveHomePathTests(unittest.TestCase):
    def test_script_exists(self):
        self.assertTrue(SCRIPT.is_file(), 'missing %s' % SCRIPT)

    def test_canonical_blog_setup_exists(self):
        self.assertTrue(CANONICAL.is_file(), 'canonical tools/qa/blog_setup.py is missing')

    def test_referenced_blog_setup_path_exists(self):
        path = referenced_blog_setup_path()
        self.assertTrue(
            path.is_file(),
            'verify-live-home.py references a non-existent blog_setup path: %s' % path)


if __name__ == '__main__':
    unittest.main()