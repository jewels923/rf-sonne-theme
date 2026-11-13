"""Contract: the home "Waveguide & Microwave" plate must not download the full-size original.

PSI (mobile) "Properly size images" flagged card-microwave.webp on the home plate:
the <img> is loading="lazy" with sizes="auto, ...". For a below-the-fold lazy image
Chrome provisionally selects the LARGEST srcset candidate before `auto` resolves, so
the full 1024w original (55838 B) was downloaded even though the plate media box only
renders ~321-370px wide. Live browser evidence: currentSrc=card-microwave.webp (full),
decodedBodySize=55838, while the box is 358x239.

Fix: cap the srcset at the already-uploaded sized variants (300w / 600w / 768w) and
drop the 1024w full candidate, so the provisional-largest pick is at most the 768
variant (34218 B). src points at a sized variant too. The 600x600 intermediate was
generated from the existing original (center-crop + LANCZOS) and uploaded to media.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / 'website' / 'home.html'

FULL = 'https://rf-sonne.com/wp-content/uploads/2026/10/card-microwave.webp'
V600 = 'https://rf-sonne.com/wp-content/uploads/2026/11/card-microwave-600x600-1.webp'


def read(path):
    if not path.is_file():
        raise AssertionError('missing %s' % path)
    return path.read_text(encoding='utf-8')


def plate_img_tag(source):
    m = re.search(r'<img\b[^>]*srcset="[^"]*card-microwave[^"]*"[^>]*>', source, re.S)
    if not m:
        raise AssertionError('card-microwave plate <img> not found in website/home.html')
    return m.group(0)


def attr(tag, name):
    m = re.search(r'\b%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


class HomePlateImageTests(unittest.TestCase):
    def setUp(self):
        self.tag = plate_img_tag(read(HOME))
        self.srcset = attr(self.tag, 'srcset') or ''
        self.src = attr(self.tag, 'src') or ''

    def test_srcset_has_600w_intermediate(self):
        self.assertIn(V600 + ' 600w', self.srcset)

    def test_srcset_keeps_300w_and_768w(self):
        self.assertIn('card-microwave-300x300.webp 300w', self.srcset)
        self.assertIn('card-microwave-768x768.webp 768w', self.srcset)

    def test_srcset_drops_full_1024w_candidate(self):
        self.assertNotIn('1024w', self.srcset)
        # The bare full original must not appear as a srcset candidate.
        self.assertNotIn(FULL + ' ', self.srcset)
        self.assertFalse(self.srcset.rstrip().endswith(FULL))

    def test_src_is_sized_variant_not_full(self):
        self.assertNotEqual(self.src, FULL)
        self.assertRegex(self.src, r'card-microwave-(?:768x768|600x600)')

    def test_plate_stays_lazy(self):
        self.assertIn('loading="lazy"', self.tag)
        self.assertIn('decoding="async"', self.tag)


if __name__ == '__main__':
    unittest.main()