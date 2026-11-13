"""Contract: non-composited animations (PSI "Avoid non-composited animations") cleared.

PSI (mobile) "避免使用未合成的动画 / Avoid non-composited animations"
(non-composited-animations, informative / not scored) flagged 37 elements on the
homepage. Chromium registers a transition animation per property and reports the
ones the compositor cannot run. The flagged unsupported properties were exactly:

  * color                  -> global `a` plus every chrome link that re-declares a
                              color transition (footer menu/contact/bottom links,
                              header email, language toggle/links, mega-menu list).
  * background-position-x/y-> the `background` shorthand transition on the
                              back-to-top button and its icon (shorthand expands
                              to non-composited background longhands).
  * border-bottom-color    -> the `border-color` transition on the sticky header
                              (border fades between the over-hero / scrolled state).
  * margin-top             -> the language caret transition.

Fix: drop those paint/layout properties from the transitions, keeping only the
compositor-friendly motion (transform / opacity) and the discrete `visibility`
step the back-to-top fade relies on. Hover colour / background changes still
happen, just instantly instead of interpolating on the main thread. The header
background is always transparent (the scroll fade lives on .site-header-shell),
so removing border-color there costs nothing visually.

This is a source-level contract: the flagged selectors must not transition any of
the non-composited properties PSI reported. The behavioural gate is a local
Lighthouse 13.6 mobile re-run of non-composited-animations (expect 0 elements).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_CSS = ROOT / 'main.css'

# Properties PSI reported as unsupported on the compositor, plus their shorthand
# parents (a `background` / `border-color` / `margin` shorthand expands to the
# flagged longhands) and the `all` keyword (animates everything).
NON_COMPOSITED = {
    'all',
    'color',
    'background', 'background-position', 'background-position-x', 'background-position-y',
    'border-color', 'border-top-color', 'border-right-color',
    'border-bottom-color', 'border-left-color',
    'margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
}

# selector -> the file it lives in. Each must transition none of NON_COMPOSITED.
TARGET_SELECTORS = [
    'a',
    '.site-utility-bar__links a',
    '.site-nav__dropdown-list a',
    '.site-header__email',
    '.site-lang__toggle',
    '.site-lang__caret',
    '.site-lang__link',
    '.site-footer__menu-list a',
    '.site-footer__contact-list a',
    '.site-footer__bottom-links a',
    '.site-footer__back-top',
    '.site-footer__back-top-icon',
    'body .site-header',
    'body.refit-chrome .site-header',
]


def read(path):
    if not path.is_file():
        raise AssertionError('missing %s' % path)
    return path.read_text(encoding='utf-8')


def split_top_level(value):
    """Split a transition value on commas that are not inside parentheses
    (cubic-bezier(...) and var(...) contain their own commas)."""
    parts = []
    depth = 0
    cur = ''
    for ch in value:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def is_time(token):
    return re.fullmatch(r'[\d.]+m?s', token) is not None or token == '0'


def is_easing(token):
    return token in {'ease', 'linear', 'ease-in', 'ease-out', 'ease-in-out',
                     'step-start', 'step-end'} or token.startswith(('cubic-bezier(', 'steps('))


def parse_rules(css):
    """Yield (selector, body) for every style rule, recursing into @media /
    @supports blocks. Comments are stripped first."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    rules = []

    def walk(start, end):
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
                walk(brace + 1, j - 1)
            elif not prelude.startswith('@'):
                rules.append((prelude, body))
            i = j

    walk(0, len(css))
    return rules


def transition_properties(body):
    """Return the set of property names a rule's transition animates. A bare
    time/easing first token (e.g. `transition: 0.2s`) means the default `all`."""
    props = set()
    for m in re.finditer(r'transition-property\s*:\s*([^;}]+)', body):
        for part in split_top_level(m.group(1)):
            tok = part.strip().split()[0] if part.strip() else ''
            if tok:
                props.add(tok)
    for m in re.finditer(r'transition\s*:\s*([^;}]+)', body):
        for part in split_top_level(m.group(1)):
            tokens = part.strip().split()
            if not tokens:
                continue
            first = tokens[0]
            if first == 'none':
                continue
            if is_time(first) or is_easing(first):
                props.add('all')
            else:
                props.add(first)
    return props


def properties_for(css, selector):
    """Union of transition properties across every rule whose selector list
    contains `selector` exactly (including @media overrides)."""
    found = False
    props = set()
    for prelude, body in parse_rules(css):
        if selector in [s.strip() for s in prelude.split(',')]:
            found = True
            props |= transition_properties(body)
    return found, props


class NonCompositedTransitionTests(unittest.TestCase):
    def setUp(self):
        self.css = read(MAIN_CSS)

    def test_flagged_selectors_exist(self):
        for selector in TARGET_SELECTORS:
            with self.subTest(selector=selector):
                found, _ = properties_for(self.css, selector)
                self.assertTrue(found, 'selector %s not found in main.css' % selector)

    def test_no_flagged_selector_transitions_non_composited_property(self):
        for selector in TARGET_SELECTORS:
            with self.subTest(selector=selector):
                _, props = properties_for(self.css, selector)
                bad = props & NON_COMPOSITED
                self.assertEqual(
                    set(), bad,
                    '%s transitions non-composited %s; keep only transform/opacity '
                    '(+ discrete visibility) so the compositor can run it' % (selector, sorted(bad)))

    def test_global_anchor_has_no_color_transition(self):
        # The root cause: every <a> inherited `transition: color`. It must be gone.
        _, props = properties_for(self.css, 'a')
        self.assertNotIn('color', props)

    def test_motion_is_preserved_where_it_existed(self):
        # The fix removes paint properties, not the composited motion itself.
        for selector in ('.site-footer__menu-list a', '.site-footer__bottom-links a',
                         '.site-nav__dropdown-list a', '.site-footer__back-top-icon'):
            with self.subTest(selector=selector):
                _, props = properties_for(self.css, selector)
                self.assertIn('transform', props)
        _, back_top = properties_for(self.css, '.site-footer__back-top')
        self.assertIn('opacity', back_top)
        self.assertIn('transform', back_top)


class ParserSanityTests(unittest.TestCase):
    """Guard the test's own CSS parser so a parsing bug can't masquerade as a pass."""

    def test_shorthand_with_cubic_bezier_and_var(self):
        body = 'transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1), color var(--transition-fast);'
        self.assertEqual({'transform', 'color'}, transition_properties(body))

    def test_bare_duration_means_all(self):
        self.assertEqual({'all'}, transition_properties('transition: 0.2s;'))

    def test_background_shorthand_is_flagged(self):
        self.assertIn('background', transition_properties('transition: transform 1s, background 1s;'))

    def test_none_is_not_a_property(self):
        self.assertEqual(set(), transition_properties('transition: none;'))

    def test_media_override_is_collected(self):
        css = '.x { transition: color 1s; } @media (max-width: 768px) { .x { transition: transform 1s; } }'
        found, props = properties_for(css, '.x')
        self.assertTrue(found)
        self.assertEqual({'color', 'transform'}, props)


if __name__ == '__main__':
    unittest.main()