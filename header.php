<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="UTF-8">
    <?php
    $sonne_fonts = get_stylesheet_directory_uri() . '/assets/fonts/';
    ?>
    <link rel="preload" href="<?php echo esc_url($sonne_fonts . 'archivo-latin-var.woff2'); ?>" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="<?php echo esc_url($sonne_fonts . 'plex-sans-latin-var.woff2'); ?>" as="font" type="font/woff2" crossorigin>
    <?php
    // GeneratePress prints the viewport meta inside wp_head. Buffer wp_head so
    // site-wide meta can be normalized and a canonical appended when Rank Math
    // omits one.
    ob_start();
    wp_head();
    $sonne_head = ob_get_clean();
    $sonne_head = function_exists('sonne_normalize_head_meta') ? sonne_normalize_head_meta($sonne_head) : $sonne_head;
    echo $sonne_head;
    if (!preg_match('/<link[^>]+rel=["\']canonical["\']/i', $sonne_head)) {
        $sonne_canonical = function_exists('sonne_current_canonical_url') ? sonne_current_canonical_url() : '';
        if ($sonne_canonical) {
            echo '<link rel="canonical" href="' . esc_url($sonne_canonical) . '" />' . "\n";
        }
    }
    ?>
</head>
<body <?php body_class(); ?>>
    <?php wp_body_open(); ?>
