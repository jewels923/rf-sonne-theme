<?php
/**
 * Private retention and expiring download links for RFQ file uploads.
 *
 * Contact Form 7 deletes uploaded files when the request ends, so copies are
 * kept for 30 days and referenced from the notification email through
 * HMAC-signed links instead of being attached to the message.
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SONNE_RFQ_FORM_ID', 171);
define('SONNE_RFQ_TOKEN_TTL', 30 * DAY_IN_SECONDS);

function sonne_rfq_private_root()
{
    $uploads = wp_upload_dir();

    if (!empty($uploads['error'])) {
        return '';
    }

    return trailingslashit($uploads['basedir']) . 'rfq-private';
}

function sonne_rfq_b64url_encode($value)
{
    return rtrim(strtr(base64_encode($value), '+/', '-_'), '=');
}

function sonne_rfq_b64url_decode($value)
{
    $value = strtr((string) $value, '-_', '+/');
    $padding = strlen($value) % 4;

    if ($padding) {
        $value .= str_repeat('=', 4 - $padding);
    }

    return base64_decode($value, true);
}

function sonne_rfq_sign(array $payload)
{
    $body = sonne_rfq_b64url_encode(wp_json_encode($payload));
    $signature = hash_hmac('sha256', $body, wp_salt('sonne_rfq_files'), true);

    return $body . '.' . sonne_rfq_b64url_encode($signature);
}

function sonne_rfq_open_token($token)
{
    $parts = explode('.', (string) $token);

    if (count($parts) !== 2) {
        return new WP_Error('sonne_rfq_invalid', 'Invalid download link.');
    }

    $body = $parts[0];
    $signature = sonne_rfq_b64url_decode($parts[1]);
    $expected = hash_hmac('sha256', $body, wp_salt('sonne_rfq_files'), true);

    if ($signature === false || !hash_equals($expected, $signature)) {
        return new WP_Error('sonne_rfq_invalid', 'Invalid download link.');
    }

    $data = json_decode((string) sonne_rfq_b64url_decode($body), true);

    if (!is_array($data) || empty($data['p']) || empty($data['e'])) {
        return new WP_Error('sonne_rfq_invalid', 'Invalid download link.');
    }

    if ($data['e'] < time()) {
        return new WP_Error('sonne_rfq_expired', 'This download link has expired.');
    }

    $root = sonne_rfq_private_root();

    if ($root === '') {
        return new WP_Error('sonne_rfq_unavailable', 'File storage is unavailable.');
    }

    $root_real = realpath($root);
    $real = realpath($root . '/' . ltrim((string) $data['p'], '/'));

    if (
        !$root_real ||
        !$real ||
        strpos($real, $root_real . DIRECTORY_SEPARATOR) !== 0 ||
        !is_file($real)
    ) {
        return new WP_Error('sonne_rfq_missing', 'File not found.');
    }

    return array(
        'path' => $real,
        'name' => !empty($data['n']) ? (string) $data['n'] : wp_basename($real),
    );
}

function sonne_rfq_serve_file(WP_REST_Request $request)
{
    $file = sonne_rfq_open_token($request->get_param('token'));

    if (is_wp_error($file)) {
        return new WP_REST_Response(array('error' => $file->get_error_code()), 404);
    }

    $ascii = preg_replace('/[^A-Za-z0-9._-]+/', '-', $file['name']);

    if (!$ascii) {
        $ascii = 'rfq-file';
    }

    nocache_headers();
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: no-referrer');
    header('Content-Type: application/octet-stream');
    header('Content-Length: ' . (string) filesize($file['path']));
    header('Content-Disposition: attachment; filename="' . $ascii . '"; filename*=UTF-8\'\'' . rawurlencode($file['name']));
    readfile($file['path']);
    exit;
}

function sonne_rfq_protect_root($root)
{
    if (!is_dir($root)) {
        return;
    }

    $htaccess = $root . '/.htaccess';

    if (!file_exists($htaccess)) {
        @file_put_contents(
            $htaccess,
            "<IfModule mod_authz_core.c>\n    Require all denied\n</IfModule>\n"
            . "<IfModule !mod_authz_core.c>\n    Order allow,deny\n    Deny from all\n</IfModule>\n"
        );
    }

    $index = $root . '/index.php';

    if (!file_exists($index)) {
        @file_put_contents($index, "<?php\n// Silence is golden.\n");
    }
}

function sonne_rfq_retain_paths(array $files)
{
    $root = sonne_rfq_private_root();

    if ($root === '') {
        return array();
    }

    sonne_rfq_protect_root($root);

    $batch = 'rfq-' . wp_generate_password(32, false, false);
    $dir = $root . '/' . $batch;

    if (!wp_mkdir_p($dir)) {
        return array();
    }

    $links = array();

    foreach ($files as $field => $paths) {
        foreach ((array) $paths as $path) {
            if (!is_string($path) || !is_file($path) || !is_readable($path)) {
                continue;
            }

            $original = wp_basename($path);
            $safe = sanitize_file_name($original);

            if ($safe === '' || $safe === '.' || $safe === '..') {
                $safe = 'rfq-file';
            }

            $target = $dir . '/' . $safe;

            if (file_exists($target)) {
                $safe = wp_generate_password(8, false, false) . '-' . $safe;
                $target = $dir . '/' . $safe;
            }

            if (!@copy($path, $target)) {
                continue;
            }

            @chmod($target, 0640);

            $token = sonne_rfq_sign(array(
                'p' => $batch . '/' . $safe,
                'n' => $original,
                'e' => time() + SONNE_RFQ_TOKEN_TTL,
            ));

            $links[$field][] = array(
                'url' => rest_url('sonne-rfq/v1/file/' . $token),
                'name' => $original,
            );
        }
    }

    if (!$links && is_dir($dir)) {
        sonne_rfq_remove_dir($dir);
    }

    return $links;
}

function sonne_rfq_retain_uploads($contact_form, &$abort, $submission)
{
    if (!($contact_form instanceof WPCF7_ContactForm) || !($submission instanceof WPCF7_Submission)) {
        return;
    }

    $form_id = (int) apply_filters('sonne_rfq_form_id', SONNE_RFQ_FORM_ID);

    if ((int) $contact_form->id() !== $form_id) {
        return;
    }

    $links = sonne_rfq_retain_paths((array) $submission->uploaded_files());

    if ($links) {
        $GLOBALS['sonne_rfq_links'] = $links;
    }
}

add_action('wpcf7_before_send_mail', 'sonne_rfq_retain_uploads', 10, 3);

function sonne_rfq_mail_tag($replaced, $submitted, $html, $mail_tag)
{
    if (
        empty($GLOBALS['sonne_rfq_links']) ||
        !is_object($mail_tag) ||
        !method_exists($mail_tag, 'field_name')
    ) {
        return $replaced;
    }

    $field = $mail_tag->field_name();

    if (!$field || empty($GLOBALS['sonne_rfq_links'][$field])) {
        return $replaced;
    }

    $lines = array();

    foreach ($GLOBALS['sonne_rfq_links'][$field] as $item) {
        if ($html) {
            $lines[] = '<a href="' . esc_url($item['url']) . '">' . esc_html($item['name']) . '</a>';
        } else {
            $lines[] = $item['name'] . ': ' . $item['url'];
        }
    }

    return $html ? implode('<br>', $lines) : implode("\n", $lines);
}

add_filter('wpcf7_mail_tag_replaced_file', 'sonne_rfq_mail_tag', 20, 4);
add_filter('wpcf7_mail_tag_replaced_file*', 'sonne_rfq_mail_tag', 20, 4);

add_action('rest_api_init', function () {
    register_rest_route('sonne-rfq/v1', '/file/(?P<token>[A-Za-z0-9._-]+)', array(
        'methods' => 'GET',
        'callback' => 'sonne_rfq_serve_file',
        'permission_callback' => '__return_true',
        'args' => array(
            'token' => array('required' => true),
        ),
    ));
});

function sonne_rfq_remove_dir($dir)
{
    if (!is_dir($dir)) {
        return;
    }

    foreach ((array) scandir($dir) as $entry) {
        if ($entry === '.' || $entry === '..') {
            continue;
        }

        $path = $dir . '/' . $entry;

        if (is_dir($path)) {
            sonne_rfq_remove_dir($path);
        } else {
            @unlink($path);
        }
    }

    @rmdir($dir);
}

function sonne_rfq_cleanup_files()
{
    $root = sonne_rfq_private_root();

    if ($root === '' || !is_dir($root)) {
        return;
    }

    $cutoff = time() - SONNE_RFQ_TOKEN_TTL;

    foreach ((array) glob($root . '/rfq-*', GLOB_ONLYDIR) as $dir) {
        if (is_dir($dir) && @filemtime($dir) < $cutoff) {
            sonne_rfq_remove_dir($dir);
        }
    }
}

add_action('sonne_rfq_cleanup', 'sonne_rfq_cleanup_files');

add_action('init', function () {
    if (!wp_next_scheduled('sonne_rfq_cleanup')) {
        wp_schedule_event(time() + HOUR_IN_SECONDS, 'daily', 'sonne_rfq_cleanup');
    }
});
