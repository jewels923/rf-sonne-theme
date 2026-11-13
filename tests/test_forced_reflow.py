"""Contract: forced synchronous layout (PSI "Forced reflow") is eliminated.

PSI (mobile) "强制自动重排 / Forced reflow" (forced-reflow-insight) flagged two
scroll-driven handlers that interleave geometry READS with style WRITES, so every
scroll frame the browser must recalculate layout synchronously:

  * assets/site-header.js:149  syncHomeHeaderState() reads homeHero.offsetHeight
    every rAF frame, then writes body class + logo.style.height/maxHeight. The
    next frame's offsetHeight read is forced because the previous frame's writes
    dirtied layout. (~64ms)
  * template-parts/footer.php  back-to-top toggleBackTop() reads window.scrollY
    on every scroll event and unconditionally toggles the is-visible class,
    forcing layout on the following read. (~26ms)

Fix (both handlers):
  * move the expensive offsetHeight read OFF the scroll path: measure the header
    threshold once on init and on resize only, cache it.
  * guard every style write behind a state-change check: during steady scrolling
    the scrolled/visible state is unchanged, so nothing is written, layout stays
    clean and subsequent reads never force a synchronous reflow.
  * rAF-batch the footer scroll read so scrollY is read at frame start (read
    before write), never mid-write.

Source-level contracts (the project has no JS render harness); the behavioural
gate is a live browser check (header scroll state + back-to-top show/hide/click)
plus a local Lighthouse mobile re-run of forced-reflow-insight.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER_JS = ROOT / 'assets/site-header.js'
FOOTER_PHP = ROOT / 'template-parts/footer.php'

LAYOUT_READS = ('offsetHeight', 'offsetWidth', 'getBoundingClientRect',
                'offsetTop', 'clientHeight', 'scrollHeight')


def read(path):
    if not path.is_file():
        raise AssertionError('missing %s' % path)
    return path.read_text(encoding='utf-8')


def function_body(source, name):
    """Return the balanced-brace body of `function name(...) {...}`."""
    m = re.search(r'function\s+%s\s*\([^)]*\)\s*\{' % re.escape(name), source)
    if not m:
        raise AssertionError('function %s not found' % name)
    i = m.end()
    depth = 1
    start = i
    while i < len(source) and depth:
        c = source[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        i += 1
    return source[start:i - 1]


class HeaderScrollReflowTests(unittest.TestCase):
    def setUp(self):
        self.js = read(HEADER_JS)
        self.sync = function_body(self.js, 'syncHomeHeaderState')

    def test_scroll_sync_does_not_read_layout_geometry(self):
        # The per-frame sync must not read any layout-forcing geometry property.
        # dataset.* reads (e.g. logo.dataset.scrollHeight) are data-attribute
        # accesses, not element geometry, so they never force layout: strip them.
        body = re.sub(r'dataset\.\w+', '', self.sync)
        for token in LAYOUT_READS:
            self.assertNotIn(token, body,
                             'syncHomeHeaderState must not read %s per frame' % token)

    def test_threshold_measured_in_dedicated_function(self):
        # offsetHeight still drives the threshold, but off the scroll path.
        measure = function_body(self.js, 'measureHeaderThreshold')
        self.assertIn('offsetHeight', measure)

    def test_scroll_sync_guards_writes_on_state_change(self):
        # Early-return when the scrolled state is unchanged so steady scrolling
        # performs zero style writes (no layout dirtying -> no forced reflow).
        self.assertIn('lastScrolled', self.sync)
        self.assertRegex(self.sync, r'isScrolled\s*===\s*lastScrolled')
        self.assertIn('return', self.sync)
        # the class write must come AFTER the guard, not before it
        self.assertLess(self.sync.index('return'),
                        self.sync.index("classList.toggle"))

    def test_resize_remeasures_threshold(self):
        m = re.search(r"addEventListener\('resize',\s*function\s*\(\)\s*\{([^}]*)\}",
                      self.js)
        self.assertIsNotNone(m, 'resize handler must re-measure the cached threshold')
        self.assertIn('measureHeaderThreshold', m.group(1))


class FooterBackTopReflowTests(unittest.TestCase):
    def setUp(self):
        self.php = read(FOOTER_PHP)

    def test_scroll_read_is_raf_batched(self):
        # scroll listener schedules a frame, it does not read scrollY directly.
        self.assertNotIn("addEventListener('scroll', toggleBackTop", self.php)
        self.assertIn('requestAnimationFrame', self.php)
        self.assertRegex(self.php, r"addEventListener\('scroll',\s*requestBackTop")

    def test_scrolly_read_inside_raf_applied_function(self):
        apply = function_body(self.php, 'applyBackTop')
        self.assertIn('window.scrollY', apply)

    def test_class_write_guarded_on_state_change(self):
        apply = function_body(self.php, 'applyBackTop')
        self.assertIn('backTopVisible', apply)
        self.assertRegex(apply, r'shouldShow\s*===\s*backTopVisible')
        self.assertIn('return', apply)
        self.assertLess(apply.index('return'),
                        apply.index("classList.toggle"))


if __name__ == '__main__':
    unittest.main()