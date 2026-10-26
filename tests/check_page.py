"""Run the P3 structural contract checks for one page slug."""
import argparse
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'p3_contract', Path(__file__).with_name('test_p3_pages.py')
)
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

CHECKS = (
    'test_source_contracts_are_complete',
    'test_fragment_shell_exact_h1_and_forbidden_markers',
    'test_source_section_sequence_and_h2s',
    'test_exact_wrapper_and_one_scoped_style',
    'test_verified_media_urls_and_nonempty_alts',
    'test_jsonld_schema_and_visible_faq_consistency',
    'test_table_regions_are_keyboard_accessible',
    'test_internal_routes_and_nonempty_hrefs',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug', choices=sorted(HARNESS.TARGETS))
    args = parser.parse_args()
    suite = unittest.TestSuite(HARNESS.P3PageTests(name) for name in CHECKS)
    with patch.dict(HARNESS.TARGETS, {args.slug: HARNESS.TARGETS[args.slug]}, clear=True):
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
