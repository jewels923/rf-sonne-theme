<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="UTF-8">
    <?php
    $sonne_fonts = get_stylesheet_directory_uri() . '/assets/fonts/';
    ?>
    <link rel="preload" href="<?php echo esc_url($sonne_fonts . 'archivo-latin-var.woff2'); ?>" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="<?php echo esc_url($sonne_fonts . 'plex-sans-latin-var.woff2'); ?>" as="font" type="font/woff2" crossorigin>
    <?php // Mono 400 (hero/plate labels) + 600 (ledger headers) are the homepage critical-chain weights; 500 is not above the fold. ?>
    <link rel="preload" href="<?php echo esc_url($sonne_fonts . 'plex-mono-latin-400.woff2'); ?>" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="<?php echo esc_url($sonne_fonts . 'plex-mono-latin-600.woff2'); ?>" as="font" type="font/woff2" crossorigin>
    <?php
    // GeneratePress prints the viewport meta inside wp_head. Buffer wp_head so
    // site-wide meta can be normalized and a canonical appended when Rank Math
    // omits one.
    ob_start();
    wp_head();
    $sonne_head = ob_get_clean();
    $sonne_head = function_exists('sonne_normalize_head_meta') ? sonne_normalize_head_meta($sonne_head) : $sonne_head;
    // 兜底：插件在打印前最后一刻仍可能塞入 Coming Soon 样式与 TP 悬浮切换器资源。
    $sonne_head = preg_replace(
        '/<link[^>]*id=["\'](?:hostinger_main_styles|trp-language-switcher(?:-v2)?)-css["\'][^>]*>\s*/i',
        '',
        $sonne_head
    );
    $sonne_head = preg_replace(
        '/<script[^>]*id=["\']trp-language-switcher-js(?:-v2)?-js["\'][^>]*>\s*<\/script>\s*/i',
        '',
        $sonne_head
    );
    echo $sonne_head;
    // 内联设计关键层：字体 @font-face + SONNE tokens/chrome/base（博客页再加 Insights）。
    // 放在 wp_head 输出之后，使 sonne 在等特异性规则上覆盖异步加载的 main.css，
    // 首屏无需任何渲染阻塞样式表。读取 .min.css 孪生体（child_theme_css_path）。
    $sonne_inline_files = array(
        child_theme_css_path('assets/css/sonne-fonts.css'),
        child_theme_css_path('sonne.css'),
    );
    if (is_home() || is_category() || is_archive() || is_singular('post') || is_page('resources') || is_search()) {
        $sonne_inline_files[] = child_theme_css_path('assets/css/sonne-insights.css');
    }
    foreach ($sonne_inline_files as $sonne_inline_rel) {
        $sonne_inline_css = child_theme_inline_css($sonne_inline_rel);
        if ($sonne_inline_css !== '') {
            echo '<style id="sonne-inline-' . esc_attr(sanitize_key(basename($sonne_inline_rel, '.css'))) . '">' . $sonne_inline_css . '</style>' . "\n";
        }
    }
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
