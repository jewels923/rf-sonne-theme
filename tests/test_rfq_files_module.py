import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'inc' / 'rfq-files.php'
FUNCTIONS = ROOT / 'functions.php'


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


class RfqFilesModuleTests(unittest.TestCase):
    def source(self):
        self.assertTrue(MODULE.is_file(), 'missing %s' % MODULE)
        return MODULE.read_text(encoding='utf-8')

    def test_module_parses_as_php(self):
        try:
            errors = php_syntax_errors(self.source())
        except ImportError as exc:
            self.skipTest('tree-sitter PHP parser unavailable: %s' % exc)
        self.assertEqual([], errors)

    def test_copies_uploads_before_cf7_deletes_them(self):
        source = self.source()
        self.assertIn("add_action('wpcf7_before_send_mail', 'sonne_rfq_retain_uploads', 10, 3)", source)
        self.assertIn('$submission->uploaded_files()', source)
        self.assertIn('rfq-private', source)

    def test_replaces_file_mail_tags_with_signed_links(self):
        source = self.source()
        self.assertIn("add_filter('wpcf7_mail_tag_replaced_file', 'sonne_rfq_mail_tag', 20, 4)", source)
        self.assertIn("add_filter('wpcf7_mail_tag_replaced_file*', 'sonne_rfq_mail_tag', 20, 4)", source)
        self.assertIn('field_name()', source)

    def test_token_is_hmac_signed_and_compared_safely(self):
        source = self.source()
        self.assertIn("hash_hmac('sha256'", source)
        self.assertIn('hash_equals(', source)
        self.assertIn("wp_salt('sonne_rfq_files')", source)

    def test_links_expire_after_30_days(self):
        source = self.source()
        self.assertIn('SONNE_RFQ_TOKEN_TTL', source)
        self.assertIn('30 * DAY_IN_SECONDS', source)
        self.assertIn('$data[\'e\'] < time()', source)

    def test_download_route_is_public_and_token_scoped(self):
        source = self.source()
        self.assertIn("register_rest_route('sonne-rfq/v1', '/file/(?P<token>", source)
        self.assertIn("'permission_callback' => '__return_true'", source)

    def test_download_is_confined_to_private_root(self):
        source = self.source()
        self.assertIn('realpath(', source)
        self.assertIn('strpos($real, $root_real . DIRECTORY_SEPARATOR) !== 0', source)
        self.assertIn('!is_file($real)', source)

    def test_download_sets_hardening_headers(self):
        source = self.source()
        for header in (
            'X-Content-Type-Options: nosniff',
            'Referrer-Policy: no-referrer',
            'Content-Type: application/octet-stream',
            'Content-Disposition: attachment',
        ):
            self.assertIn(header, source)
        self.assertIn('readfile(', source)

    def test_upload_directory_is_denied_by_server(self):
        source = self.source()
        self.assertIn('Require all denied', source)
        self.assertIn('Deny from all', source)
        self.assertIn("'/.htaccess'", source)
        self.assertIn("'/index.php'", source)

    def test_old_batches_are_cleaned_daily(self):
        source = self.source()
        self.assertIn("'sonne_rfq_cleanup'", source)
        self.assertIn('wp_schedule_event(', source)
        self.assertIn('sonne_rfq_remove_dir(', source)

    def test_only_the_rfq_form_is_processed(self):
        source = self.source()
        self.assertIn('define(\'SONNE_RFQ_FORM_ID\', 171)', source)
        self.assertIn("apply_filters('sonne_rfq_form_id'", source)

    def test_does_not_dump_or_log_submission_data(self):
        source = self.source()
        for call in ('var_dump(', 'print_r(', 'error_log('):
            self.assertNotIn(call, source)

    def test_functions_php_loads_module_with_guard(self):
        source = FUNCTIONS.read_text(encoding='utf-8')
        self.assertIn("if (file_exists($child_dir . '/inc/rfq-files.php')) {", source)
        self.assertIn("require_once $child_dir . '/inc/rfq-files.php';", source)


if __name__ == '__main__':
    unittest.main()
