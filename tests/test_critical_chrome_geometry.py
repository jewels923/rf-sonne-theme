"""Contract: the inline critical layer (sonne.css) reserves chrome geometry.

Root cause (browser-measured, task #227): on a cold cache the homepage paints
with an unstyled, expanded header before main.min.css arrives ~260ms later.
The async GP-parent + main.min.css links print inside wp_head(); the inline
design layer (sonne-fonts + sonne + insights) prints AFTER them, so the cascade
is GP < main < sonne < insights and sonne wins equal-specificity rules.

sonne.css currently styles chrome COLOUR only (background / min-height / font).
Every chrome LAYOUT rule lives solely in main.css, which is render-deferred. So
at first paint the header is in normal flow (~3103px tall), the nav list is a
vertical block (~1409px), and dropdowns render expanded in-flow. When main.css
lands the header collapses to an 84px fixed bar and the whole viewport shifts:
CLS ~= 1.019 cold, 0 warm.

Fix: copy the first-paint-critical chrome LAYOUT declarations from main.css into
sonne.css so the inline layer reserves the final geometry before main.css loads.
Values are taken verbatim from main.css (the live, warm-cache layout) so the
warm rendering is unchanged; only the cold first paint stops shifting.

Scope guards baked into this contract:
  * The 8 "drift" rules where sonne already differs from main and WINS the
    cascade (utility-bar font 0.68rem, header inner 84/72px, nav link / menu
    toggle / mobile close min-height 44px) must be preserved, not reconciled.
  * No `body.refit-chrome ...` selector may be introduced: that class is never
    added by any PHP/JS/HTML, so those main.css rules are dead code.

This is a source-level contract against sonne.css (the editable source; the
shipped sonne.min.css twin is regenerated from it by tools/minify_css.py). The
behavioural gate is a cold-load CLS re-measure (target <= 0.1, baseline ~1.019).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SONNE_CSS = ROOT / 'sonne.css'


def read(path):
    if not path.is_file():
        raise AssertionError('missing %s' % path)
    return path.read_text(encoding='utf-8')


def parse_rules(css):
    """Yield (selector, body, media) for every style rule. `media` is the
    enclosing @media / @supports prelude ('' at top level). Comments stripped."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    rules = []

    def walk(start, end, media):
        i = start
        while i < end:
            brace = css.find('{', i, end)
            if brace == -1:
                break
            prelude = css[i:brace].strip()
            depth = 1
            j = brace + 1
            while j < end and depth:
                if css[j] == '{':
                    depth += 1
                elif css[j] == '}':
                    depth -= 1
                j += 1
            body = css[brace + 1:j - 1]
            if prelude.startswith('@media') or prelude.startswith('@supports'):
                walk(brace + 1, j - 1, prelude)
            elif not prelude.startswith('@'):
                rules.append((prelude, body, media))
            i = j

    walk(0, len(css), '')
    return rules


def declarations(body):
    """property -> value (last wins, whitespace collapsed) for a leaf rule body."""
    decls = {}
    for part in body.split(';'):
        if ':' not in part:
            continue
        prop, _, val = part.partition(':')
        prop = prop.strip().lower()
        val = ' '.join(val.split())
        if prop and val:
            decls[prop] = val
    return decls


def rules_for(css, selector):
    """Every (media, decls) whose comma-split selector list contains `selector`."""
    out = []
    for prelude, body, media in parse_rules(css):
        if selector in [s.strip() for s in prelude.split(',')]:
            out.append((media, declarations(body)))
    return out


def base_decls(css, selector):
    """Merged declarations from top-level (non-@media) rules for `selector`."""
    merged = {}
    for media, decls in rules_for(css, selector):
        if media == '':
            merged.update(decls)
    return merged


def media_decls(css, selector, media_substr):
    """Merged declarations for `selector` inside any @media whose prelude
    contains `media_substr` (e.g. 'max-width: 1024px')."""
    merged = {}
    for media, decls in rules_for(css, selector):
        if media_substr in media:
            merged.update(decls)
    return merged


# --- Group 1-6: first-paint-critical chrome LAYOUT, taken verbatim from main.css.
# selector -> {property: expected value} that must exist in the BASE context.
BASE_GEOMETRY = {
    # Group 1: header skeleton (the CLS culprit).
    'body .site-header-shell': {
        'position': 'fixed', 'top': '0', 'left': '0', 'right': '0', 'z-index': '9999',
    },
    'body .site-header': {'position': 'relative !important'},
    '.site-header__inner': {
        'display': 'flex', 'align-items': 'center',
        'justify-content': 'space-between', 'position': 'static',
    },
    '.site-header .inside-header': {
        'display': 'flex', 'max-width': '1440px !important', 'margin': '0 auto',
    },
    '.site-header .container-xl': {
        'display': 'flex', 'max-width': '1440px !important', 'margin': '0 auto',
    },
    # The actions box holds email + language + CTA on one row; without flex it
    # stacks them vertically at first paint and inflates the header height.
    '.site-header__actions': {
        'display': 'flex', 'align-items': 'center', 'height': '100%',
        'flex-shrink': '0', 'gap': '0.625rem', 'margin-left': '0',
    },
    '.site-content': {'padding-top': '0 !important'},
    '.generate-sections-inside-container': {'padding-top': '0 !important'},
    '.top-bar': {'display': 'none !important'},
    '.site-utility-bar': {'display': 'none !important'},
    # Group 2: branding.
    '.site-branding': {'flex-shrink': '0'},
    '.site-branding__link': {'display': 'inline-flex', 'align-items': 'center'},
    '.site-branding__logo': {'display': 'block', 'width': 'auto', 'max-height': '43px'},
    # Group 3: nav / dropdown.
    '.site-nav': {'margin-left': 'auto'},
    '.site-nav__list': {
        'display': 'flex', 'align-items': 'center', 'justify-content': 'flex-end',
    },
    '.site-nav__item': {'display': 'flex', 'position': 'relative', 'align-items': 'center'},
    '.site-nav__link': {'display': 'inline-flex', 'white-space': 'nowrap'},
    '.site-nav__caret': {'display': 'inline-block'},
    '.site-nav__dropdown': {'position': 'absolute', 'top': '100%', 'visibility': 'hidden'},
    '.site-nav__dropdown--mega': {'left': '50%', 'width': '95vw', 'max-width': '900px'},
    '.site-nav__item:hover > .site-nav__dropdown': {'visibility': 'visible'},
    '.site-nav__item:focus-within > .site-nav__dropdown': {'visibility': 'visible'},
    # Group 4: header email.
    '.site-header__email': {'display': 'inline-flex', 'white-space': 'nowrap', 'flex': 'none'},
    '.site-header__email-icon': {'width': '18px', 'height': '18px', 'flex': 'none'},
    # Group 5: language switcher.
    '.site-lang': {'position': 'relative', 'display': 'flex', 'align-items': 'center'},
    '.site-lang__toggle': {'display': 'inline-flex', 'align-items': 'center'},
    '.site-lang__globe': {'width': '15px', 'height': '15px'},
    '.site-lang__panel': {
        'position': 'absolute', 'inset-inline-end': '0', 'z-index': '120', 'overflow-y': 'auto',
    },
    # Group 6: mobile toggle / drawer.
    '.site-menu-toggle': {'display': 'none', 'width': '48px'},
    '.site-menu-toggle span': {'display': 'block', 'height': '2px'},
    '.site-mobile-nav': {'position': 'fixed', 'inset': '0', 'z-index': '30'},
    'body.site-nav-open': {'overflow': 'hidden'},
}

# selector -> {property: value} that must exist inside a specific @media block.
MEDIA_GEOMETRY = [
    ('.site-nav--desktop', 'max-width: 1024px', {'display': 'none'}),
    ('.site-header__catalog', 'max-width: 1024px', {'display': 'none'}),
    ('.site-menu-toggle', 'max-width: 1024px', {'display': 'grid'}),
    ('.site-branding__tagline', 'max-width: 768px', {'display': 'none'}),
    ('.site-nav__link', 'min-width: 1025px', {'font-size': '13px'}),
]

# --- The 8 drift rules: sonne already wins the cascade; values must NOT change.
DRIFT_BASE = {
    '.site-utility-bar': {'font-size': '0.68rem'},
    '.site-utility-bar__inner': {'min-height': '44px'},
    '.site-utility-bar__links a': {'display': 'inline-flex', 'min-height': '44px'},
    'body .site-header__inner': {'min-height': '84px'},
    '.site-nav__link': {'min-height': '44px'},
    '.site-menu-toggle': {'min-width': '44px', 'min-height': '44px'},
    '.site-mobile-nav__close': {'min-height': '44px'},
    '.site-mobile-nav__toggle': {'min-height': '44px'},
}
DRIFT_MEDIA = [
    ('body .site-header__inner', 'max-width: 768px', {'min-height': '72px'}),
]


class CriticalChromeGeometryTests(unittest.TestCase):
    """The new behaviour: sonne.css reserves chrome layout at first paint."""

    def setUp(self):
        self.css = read(SONNE_CSS)

    def test_base_chrome_geometry_is_inlined(self):
        for selector, expected in BASE_GEOMETRY.items():
            decls = base_decls(self.css, selector)
            for prop, value in expected.items():
                with self.subTest(selector=selector, prop=prop):
                    self.assertEqual(
                        value, decls.get(prop),
                        '%s must declare %s: %s in sonne.css (inline critical layer) '
                        'so first paint reserves chrome geometry before main.css loads; '
                        'got %r' % (selector, prop, value, decls.get(prop)))

    def test_responsive_chrome_geometry_is_inlined(self):
        for selector, media, expected in MEDIA_GEOMETRY:
            decls = media_decls(self.css, selector, media)
            for prop, value in expected.items():
                with self.subTest(selector=selector, media=media, prop=prop):
                    self.assertEqual(
                        value, decls.get(prop),
                        '%s must declare %s: %s inside @media (%s) in sonne.css; '
                        'got %r' % (selector, prop, value, media, decls.get(prop)))


class DriftPreservationTests(unittest.TestCase):
    """sonne already wins these equal-specificity rules; do not reconcile them."""

    def setUp(self):
        self.css = read(SONNE_CSS)

    def test_drift_base_values_preserved(self):
        for selector, expected in DRIFT_BASE.items():
            decls = base_decls(self.css, selector)
            for prop, value in expected.items():
                with self.subTest(selector=selector, prop=prop):
                    self.assertEqual(
                        value, decls.get(prop),
                        '%s %s must stay %s (sonne wins the cascade over main.css); '
                        'got %r' % (selector, prop, value, decls.get(prop)))

    def test_drift_media_values_preserved(self):
        for selector, media, expected in DRIFT_MEDIA:
            decls = media_decls(self.css, selector, media)
            for prop, value in expected.items():
                with self.subTest(selector=selector, media=media, prop=prop):
                    self.assertEqual(value, decls.get(prop),
                                     '%s %s must stay %s inside @media (%s); got %r'
                                     % (selector, prop, value, media, decls.get(prop)))


class NoDeadRefitChromeTests(unittest.TestCase):
    """`refit-chrome` is never added to <body>; its rules are dead code."""

    def test_sonne_has_no_refit_chrome_selector(self):
        css = read(SONNE_CSS)
        for prelude, _body, _media in parse_rules(css):
            self.assertNotIn('refit-chrome', prelude,
                             'sonne.css must not introduce dead body.refit-chrome rules')


class ParserSanityTests(unittest.TestCase):
    """Guard the test's own CSS parser so a parsing bug can't fake a pass/fail."""

    def test_base_and_media_are_separated(self):
        css = ('.x { display: none; } '
               '@media (max-width: 1024px) { .x { display: grid; } }')
        self.assertEqual({'display': 'none'}, base_decls(css, '.x'))
        self.assertEqual({'display': 'grid'}, media_decls(css, '.x', 'max-width: 1024px'))

    def test_comma_selector_list_matches_each_member(self):
        css = '.top-bar, .site-utility-bar { display: none !important; }'
        self.assertEqual({'display': 'none !important'}, base_decls(css, '.top-bar'))
        self.assertEqual({'display': 'none !important'}, base_decls(css, '.site-utility-bar'))

    def test_descendant_combinator_is_not_split_on_comma(self):
        css = '.site-header .inside-header { display: flex; max-width: 1440px !important; }'
        self.assertEqual('flex', base_decls(css, '.site-header .inside-header')['display'])
        self.assertEqual({}, base_decls(css, '.inside-header'))

    def test_important_and_whitespace_are_normalised(self):
        css = '.site-content { padding-top: 0   !important; }'
        self.assertEqual('0 !important', base_decls(css, '.site-content')['padding-top'])

    def test_comments_are_stripped(self):
        css = '/* .x { display: flex; } */ .x { position: static; }'
        self.assertEqual({'position': 'static'}, base_decls(css, '.x'))

    def test_child_combinator_selector_matches(self):
        css = '.site-nav__item:hover > .site-nav__dropdown { visibility: visible; }'
        self.assertEqual(
            {'visibility': 'visible'},
            base_decls(css, '.site-nav__item:hover > .site-nav__dropdown'))

    def test_keyframes_and_font_face_do_not_leak(self):
        css = ('@keyframes spin { from { opacity: 0; } to { opacity: 1; } } '
               '@font-face { font-family: x; src: url(a.woff2); } '
               '.site-nav { margin-left: auto; }')
        self.assertEqual({'margin-left': 'auto'}, base_decls(css, '.site-nav'))
        self.assertEqual({}, base_decls(css, 'from'))


if __name__ == '__main__':
    unittest.main()