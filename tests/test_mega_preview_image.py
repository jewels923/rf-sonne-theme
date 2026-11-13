"""Contract: the hidden mega-menu product preview must not eager-load the full-size image.

PSI (mobile) "Improve image delivery" flagged card-microwave.webp: the full 1024px
original (54.5 KiB) was downloaded on every page load even though the preview box is
hidden until hover and only renders ~380px. Root cause: template-parts/header.php
rendered <img id="productPreviewImg"> eager (no loading attr) at the full-size URL,
and every hover-trigger data-img fell back to that same full-size default.

Fix: serve an already-generated sized variant (768x768) and defer the hidden image
with loading="lazy" + decoding="async", so no full-size request happens on first
paint. The helper only maps to variants that already exist on disk (no new images).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / 'functions.php'
HEADER_PART = ROOT / 'template-parts' / 'header.php'


def read(path):
    if not path.is_file():
        raise AssertionError('missing %s' % path)
    return path.read_text(encoding='utf-8')


def preview_img_tag(source):
    m = re.search(r'<img\b(?:\?>|[^>])*id="productPreviewImg"(?:\?>|[^>])*>', source, re.S)
    if not m:
        raise AssertionError('productPreviewImg <img> not found in template-parts/header.php')
    return m.group(0)


class PreviewImageDeferralTests(unittest.TestCase):
    def setUp(self):
        self.header = read(HEADER_PART)
        self.tag = preview_img_tag(self.header)

    def test_preview_img_is_lazy_and_async_decoded(self):
        self.assertIn('loading="lazy"', self.tag)
        self.assertIn('decoding="async"', self.tag)

    def test_preview_img_src_uses_sized_variant_helper(self):
        self.assertIn('child_theme_preview_src(', self.tag)

    def test_hover_data_img_uses_sized_variant_helper(self):
        m = re.search(r'data-img="<\?php[^>]*?\?>"', self.header, re.S)
        self.assertIsNotNone(m, 'data-img attribute not found')
        self.assertIn('child_theme_preview_src(', m.group(0))


class PreviewVariantHelperTests(unittest.TestCase):
    def setUp(self):
        self.functions = read(FUNCTIONS)

    def test_helper_defined(self):
        self.assertIn('function child_theme_preview_src(', self.functions)

    def test_helper_maps_to_existing_variant_with_existence_check(self):
        self.assertIn('-768x768', self.functions)
        self.assertIn('file_exists(', self.functions)

    def test_helper_does_not_generate_new_images(self):
        # Only string-mapping + existence checks; never invoke the WP image editor
        # or regenerate metadata (no new image files may be created).
        self.assertNotIn('wp_generate_attachment_metadata', self.functions)
        self.assertNotIn('WP_Image_Editor', self.functions)


if __name__ == '__main__':
    unittest.main()