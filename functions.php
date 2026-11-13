<?php
/**
 * Infility GP Child Theme — functions.php（通用模板版）
 *
 * 安全原则：所有文件引用都用 file_exists() 保护，缺文件不会导致崩溃。
 * 使用前请全局搜索 "TODO" 替换为你自己的站点信息。
 */

// ============================================================
// 引入可选组件（缺文件自动跳过，不会崩溃）
// ============================================================
$child_dir = get_stylesheet_directory();

// 面包屑短代码 [breadcrumb]
if (file_exists($child_dir . '/inc/breadcrumb.php')) {
    require_once $child_dir . '/inc/breadcrumb.php';
}

// RFQ 上传文件私密留存与签名下载链接
if (file_exists($child_dir . '/inc/rfq-files.php')) {
    require_once $child_dir . '/inc/rfq-files.php';
}

// SONNE Insights blog helpers
if (file_exists($child_dir . '/inc/insights.php')) {
    require_once $child_dir . '/inc/insights.php';
}

// 悬浮 WhatsApp 对话框
if (file_exists($child_dir . '/inc/whatsapp-chat.php')) {
    require_once $child_dir . '/inc/whatsapp-chat.php';
}

// WPAI 模块（可选，没有就跳过）
if (file_exists($child_dir . '/wpai/bootstrap.php')) {
    require_once $child_dir . '/wpai/bootstrap.php';
    if (class_exists('\Infility\WPAI\Preview\Chat')) {
        \Infility\WPAI\Preview\Chat::init();
    }
    if (class_exists('\Infility\WPAI\Admin\Settings')) {
        \Infility\WPAI\Admin\Settings::init();
    }
}

// ============================================================
// 资源加载（版本号 = 文件修改时间，改 CSS/JS 后自动刷新缓存）
// ============================================================
function child_theme_asset_version($relative_path) {
    $absolute_path = get_stylesheet_directory() . '/' . ltrim($relative_path, '/');
    if (!file_exists($absolute_path)) {
        return null;
    }
    return (string) filemtime($absolute_path);
}

// Serve the csso-minified twin when present; sources stay editable for tests/preview.
function child_theme_css_path($relative_path) {
    $min = preg_replace('/\.css$/', '.min.css', $relative_path);
    if ($min !== $relative_path && file_exists(get_stylesheet_directory() . '/' . $min)) {
        return $min;
    }
    return $relative_path;
}

// Read a stylesheet for inlining into <head>. Relative url(./|../) tokens resolve
// against the document root once inlined (not the CSS file's dir), so rebase them
// onto the stylesheet's own directory URI — otherwise @font-face src '../fonts/x'
// 404s at /fonts/x. Absolute, root-relative, data: and fragment URLs are left as-is.
function child_theme_inline_css($relative_path) {
    $absolute_path = get_stylesheet_directory() . '/' . $relative_path;
    if (!file_exists($absolute_path)) {
        return '';
    }
    $css = file_get_contents($absolute_path);
    $dir = str_replace('\\', '/', dirname($relative_path));
    $base = trailingslashit(get_stylesheet_directory_uri() . ($dir === '.' ? '' : '/' . $dir));
    return preg_replace_callback(
        '/url\(\s*([\'"]?)(\.\.?\/[^\'")]+)\1\s*\)/i',
        function ($m) use ($base) {
            return 'url(' . $m[1] . $base . $m[2] . $m[1] . ')';
        },
        $css
    );
}

// The mega-menu preview box stays hidden until hover and renders only ~380px, so
// serving the full-size original downloads wasted bytes on every page load. Map the
// URL to an already-generated square variant when that file exists on disk; fall back
// to the original otherwise. Never creates new image files.
function child_theme_preview_src($url) {
    $url = (string) $url;
    if ($url === '' || !preg_match('/\.webp$/i', $url)) {
        return $url;
    }
    $upload = wp_get_upload_dir();
    if (empty($upload['baseurl']) || empty($upload['basedir']) || strpos($url, $upload['baseurl']) !== 0) {
        return $url;
    }
    $relative = substr($url, strlen($upload['baseurl']));
    foreach (array('-768x768', '-300x300') as $suffix) {
        $variant = preg_replace('/\.webp$/i', $suffix . '.webp', $relative);
        if (file_exists($upload['basedir'] . $variant)) {
            return $upload['baseurl'] . $variant;
        }
    }
    return $url;
}

function child_theme_enqueue_assets() {
    // 渲染阻塞优化：设计关键层（sonne-fonts + sonne，博客页加 sonne-insights）由
    // header.php 内联进 <head>，首屏无需阻塞请求。这里只登记重的遗留层（GP 父主题 +
    // main.css），再由 child_theme_async_style_tag 转为异步加载（保留外部缓存）。

    // 父主题样式（异步）
    wp_enqueue_style('generate-style');

    // 主设计系统 main.css（异步）
    $main_css = child_theme_css_path('main.css');
    if (file_exists(get_stylesheet_directory() . '/' . $main_css)) {
        wp_enqueue_style(
            'child-theme-main-css',
            get_stylesheet_directory_uri() . '/' . $main_css,
            array('generate-style'),
            child_theme_asset_version($main_css)
        );
    }

    // 页头行为脚本（可选）
    if (file_exists(get_stylesheet_directory() . '/assets/site-header.js')) {
        wp_enqueue_script(
            'child-theme-site-header',
            get_stylesheet_directory_uri() . '/assets/site-header.js',
            array(),
            child_theme_asset_version('assets/site-header.js'),
            false
        );
    }

    // WhatsApp 浮动对话框脚本
    if (file_exists(get_stylesheet_directory() . '/assets/whatsapp-chat.js')) {
        wp_enqueue_script(
            'child-theme-whatsapp-chat',
            get_stylesheet_directory_uri() . '/assets/whatsapp-chat.js',
            array(),
            child_theme_asset_version('assets/whatsapp-chat.js'),
            false
        );
    }
}
add_action('wp_enqueue_scripts', 'child_theme_enqueue_assets');

// 关键请求链优化：页头 / WhatsApp / GP 导航三个行为脚本改为 <head> 内 defer。
// 它们原先排在页脚且无 defer，预加载扫描器要到 HTML 流末尾才发现，形成
// “文档 → 脚本” 的串行关键链（PSI 关键路径延迟 618ms）。defer 让扫描器在流开头
// 即发现并以低优先级并行下载（链深降为 1），执行仍推迟到解析完成后，DOM 已就绪，
// 行为不变（两个子主题脚本本就带 DOMContentLoaded 守卫）。
function child_theme_defer_behavior_scripts($tag, $handle, $src) {
    if (!in_array($handle, array('child-theme-site-header', 'child-theme-whatsapp-chat', 'generate-menu'), true)) {
        return $tag;
    }
    if (strpos($tag, ' defer') !== false) {
        return $tag;
    }
    return str_replace(' src=', ' defer src=', $tag);
}
add_filter('script_loader_tag', 'child_theme_defer_behavior_scripts', 10, 3);

// GP 导航脚本默认排在页脚；移到 <head> 配合上面的 defer 以尽早被扫描器发现。
function child_theme_head_behavior_scripts() {
    wp_script_add_data('generate-menu', 'group', 0);
}
add_action('wp_enqueue_scripts', 'child_theme_head_behavior_scripts', 20);

// 把重的遗留样式表（GP 父主题 + main.css）转为非阻塞：rel=preload as=style，
// onload 后切换为 stylesheet，并提供 noscript 回退。设计关键层已内联，首屏不受
// 这些请求阻塞；级联顺序由 DOM 位置保证（异步 link 在 wp_head 内，内联层在其后）。
function child_theme_async_style_tag($html, $handle, $href, $media) {
    if (!in_array($handle, array('generate-style', 'child-theme-main-css'), true)) {
        return $html;
    }
    $preload = '<link rel="preload" as="style" href="' . esc_url($href) . '" onload="this.onload=null;this.rel=\'stylesheet\'">';
    $fallback = '<noscript><link rel="stylesheet" href="' . esc_url($href) . '"></noscript>';
    return $preload . "\n" . $fallback;
}
add_filter('style_loader_tag', 'child_theme_async_style_tag', 10, 4);

// ============================================================
// 资源裁剪
// hCaptcha / CF7 只在含表单的两页加载；其余页面移除 WP 内核与插件样式。
// ============================================================
function child_theme_is_form_page() {
    return is_page('contact') || is_page('request-a-quote');
}

function child_theme_prune_assets() {
    foreach (array(
        'wp-block-library',
        'wp-block-library-theme',
        'classic-theme-styles',
        'global-styles',
        'wp-emoji-styles',
        'wp-img-auto-sizes-contain',
        'wp-img-auto-sizes',
        'hostinger_main_styles',
        'generate-child',
        // 页头语言切换器是主题自带的 details/summary，TranslatePress 的悬浮切换器资源用不上。
        'trp-language-switcher-v2',
        'trp-language-switcher',
        'trp-frontend-language-switcher',
    ) as $handle) {
        wp_dequeue_style($handle);
        wp_deregister_style($handle);
    }

    foreach (array(
        'trp-language-switcher-js-v2',
        'trp-language-switcher-js',
        'trp-frontend-language-switcher',
    ) as $handle) {
        wp_dequeue_script($handle);
        wp_deregister_script($handle);
    }

    if (child_theme_is_form_page()) {
        return;
    }

    foreach (array(
        'contact-form-7',
        'swv',
        'wp-hooks',
        'wp-i18n',
        'cf7apps-redirection',
        'cf7apps-honeypot-frontend',
        'jquery',
        'jquery-core',
        'jquery-migrate',
    ) as $handle) {
        wp_dequeue_script($handle);
        wp_deregister_script($handle);
    }
    wp_dequeue_style('contact-form-7');
    wp_dequeue_style('cf7apps-honeypot-frontend');
}
add_action('wp_enqueue_scripts', 'child_theme_prune_assets', 100);

// Hostinger 与 TranslatePress 在优先级 100 之后仍会登记资源；
// 在打印前的最后一刻再摘一次，保证 Coming Soon 样式与 TP 切换器资源不出现在真实页面。
function child_theme_prune_assets_late() {
    foreach (array('hostinger_main_styles', 'trp-language-switcher-v2', 'trp-language-switcher') as $handle) {
        wp_dequeue_style($handle);
    }
    foreach (array('trp-language-switcher-js-v2', 'trp-language-switcher-js') as $handle) {
        wp_dequeue_script($handle);
    }
}
add_action('wp_print_styles', 'child_theme_prune_assets_late', 0);
add_action('wp_print_scripts', 'child_theme_prune_assets_late', 0);

// Emoji 探测脚本与样式全站无用
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');
remove_action('admin_print_scripts', 'print_emoji_detection_script');
remove_action('admin_print_styles', 'print_emoji_styles');

// CF7 Apps 把 hCaptcha loader 直接 echo 在 wp_footer。两套表单都没有
// .h-captcha 字段，loader 只会白白拉取 ~390KB，这里整段剥掉。
// 若日后表单真的加入 hCaptcha 字段，需同步移除这段过滤。
function child_theme_start_footer_buffer() {
    ob_start();
}

function child_theme_strip_footer_scripts() {
    $output = ob_get_clean();
    if (!is_string($output) || $output === '') {
        return;
    }
    $output = preg_replace(
        '#<script[^>]+src=["\']https://js\.hcaptcha\.com/1/api\.js[^"\']*["\'][^>]*>\s*</script>#i',
        '',
        $output
    );
    $output = preg_replace(
        '#<script[^>]*>\s*var CF7AppsLoadhCaptcha[\s\S]*?</script>#i',
        '',
        $output
    );
    echo $output;
}
add_action('wp_footer', 'child_theme_start_footer_buffer', -9999);
add_action('wp_footer', 'child_theme_strip_footer_scripts', 9999);

// ============================================================
// 匿名 HTML 缓存头
// 上线（关闭 Coming Soon）后把 SONNE_HTML_CACHE 改为 true；
// 维护页在线时保持 false，避免 hcdn 缓存住 Coming Soon 页面。
// ============================================================
if (!defined('SONNE_HTML_CACHE')) {
    define('SONNE_HTML_CACHE', false);
}

add_action('send_headers', function () {
    if (!SONNE_HTML_CACHE || is_admin() || is_user_logged_in() || is_404() || is_preview() || is_feed()) {
        return;
    }
    if (!isset($_SERVER['REQUEST_METHOD']) || $_SERVER['REQUEST_METHOD'] !== 'GET') {
        return;
    }
    if (child_theme_is_form_page()) {
        return;
    }
    header('Cache-Control: public, max-age=300, s-maxage=86400, stale-while-revalidate=86400');
    header_remove('Expires');
    header_remove('Pragma');
    header_remove('Set-Cookie');
});

// ============================================================
// 注入自定义 header / footer（替换 GeneratePress 默认）
// ============================================================
if (!is_admin()) {
    // 移除 GP 默认 header
    remove_action('generate_before_header', 'generate_display_header');

    // 注入自定义 header（如果模板没有自己输出）
    add_action('generate_before_content', function () {
        if (!empty($GLOBALS['child_header_emitted'])) {
            return;
        }
        if (locate_template('template-parts/header.php')) {
            get_template_part('template-parts/header');
        }
    }, 20);

    // 注入自定义 footer
    add_action('generate_after_main_content', function () {
        if (locate_template('template-parts/footer.php')) {
            get_template_part('template-parts/footer');
        }
    }, 25);
}

// ============================================================
// 页头语言切换器（源码来自 TranslatePress 已发布语言）
// ============================================================
function sonne_language_switcher_items() {
    static $items = null;
    if ($items !== null) {
        return $items;
    }

    $items = array('current' => '', 'current_name' => '', 'languages' => array());
    if (!function_exists('trp_get_languages') || !class_exists('TRP_Translate_Press')) {
        return $items;
    }

    $trp = TRP_Translate_Press::get_trp_instance();
    $settings = $trp->get_component('settings')->get_settings();
    $converter = $trp->get_component('url_converter');
    $languages = $trp->get_component('languages')->get_language_names($settings['publish-languages'], 'native_name');
    $current = !empty($GLOBALS['TRP_LANGUAGE']) ? $GLOBALS['TRP_LANGUAGE'] : $settings['default-language'];

    foreach ($languages as $code => $name) {
        $short = strtoupper(explode('_', $code)[0]);
        $items['languages'][] = array(
            'code' => $code,
            'name' => $name,
            'short' => $short,
            'url' => str_replace('#TRPLINKPROCESSED', '', $converter->get_url_for_language($code, false)),
            'is_current' => ($code === $current),
        );
        if ($code === $current) {
            $items['current'] = $short;
            $items['current_name'] = $name;
        }
    }

    if ($items['current'] === '' && !empty($items['languages'])) {
        $items['current'] = $items['languages'][0]['short'];
        $items['current_name'] = $items['languages'][0]['name'];
    }

    return $items;
}

// ============================================================
// 最新文章短代码 [latest_posts]
// ============================================================
function child_latest_posts_shortcode($atts) {
    $atts = shortcode_atts(array('count' => 3), $atts);
    $query = new WP_Query(array(
        'post_type'      => 'post',
        'posts_per_page' => intval($atts['count']),
        'post_status'    => 'publish',
    ));

    $html = '<div class="grid-3">';
    if ($query->have_posts()) {
        while ($query->have_posts()) {
            $query->the_post();
            $thumbnail_url = get_the_post_thumbnail_url(get_the_ID(), 'medium_large');
            $title   = get_the_title();
            $excerpt = wp_trim_words(get_the_excerpt(), 15);
            $link    = get_permalink();
            $categories = get_the_category();
            $cat_name = !empty($categories) ? esc_html($categories[0]->name) : 'Insight';

            $html .= '<a href="' . esc_url($link) . '" class="card insight-card reveal">';
            if ($thumbnail_url) {
                $html .= '<div class="insight-card__media" style="background-image: url(\'' . esc_url($thumbnail_url) . '\')"></div>';
            }
            $html .= '<div class="insight-card__body">';
            $html .= '<div class="card-tag">Latest · ' . $cat_name . '</div>';
            $html .= '<h3 class="insight-card__title">' . esc_html($title) . '</h3>';
            $html .= '<p class="insight-card__copy">' . esc_html($excerpt) . '</p>';
            $html .= '<span class="card-cta">Read article</span>';
            $html .= '</div></a>';
        }
        wp_reset_postdata();
    } else {
        $html .= '<p>No posts found.</p>';
    }
    $html .= '</div>';
    return $html;
}
add_shortcode('latest_posts', 'child_latest_posts_shortcode');

// ============================================================
// 主题激活时自动部署（安全版：只复制不删除，路径不硬编码）
// ============================================================
add_action('after_switch_theme', function () {
    $child_dir  = get_stylesheet_directory();
    $source_dir = $child_dir . '/infility-theme-plugin';

    // 1. 部署 trans.php（生成随机 AUTH_TOKEN）
    $trans_source = $source_dir . '/trans.php';
    $trans_target = $child_dir . '/trans.php';
    if (file_exists($trans_source) && !file_exists($trans_target)) {
        $auth_token = bin2hex(random_bytes(5));
        $content = file_get_contents($trans_source);
        $content = str_replace("define('AUTH_TOKEN', '');", "define('AUTH_TOKEN', '{$auth_token}');", $content);
        file_put_contents($trans_target, $content);
        set_transient('infility_auth_token', $auth_token, 300);
    }

    // 2. 部署 SEO Bridge 到 mu-plugins（复制，不删除源文件）
    $bridge_source = $source_dir . '/universal-seo-bridge.php';
    $mu_dir = WP_CONTENT_DIR . '/mu-plugins';
    if (file_exists($bridge_source)) {
        if (!is_dir($mu_dir)) {
            wp_mkdir_p($mu_dir);
        }
        if (!file_exists($mu_dir . '/universal-seo-bridge.php')) {
            copy($bridge_source, $mu_dir . '/universal-seo-bridge.php');
        }
    }

    // 3. 复制父主题截图（可选）
    $parent_screenshot = WP_CONTENT_DIR . '/themes/generatepress/screenshot.png';
    $child_screenshot  = $child_dir . '/screenshot.png';
    if (file_exists($parent_screenshot) && !file_exists($child_screenshot)) {
        copy($parent_screenshot, $child_screenshot);
    }
});

// 激活后弹窗提示 AUTH_TOKEN
add_action('admin_notices', function () {
    $auth_token = get_transient('infility_auth_token');
    if ($auth_token) {
        delete_transient('infility_auth_token');
        echo '<div class="notice notice-success is-dismissible" style="padding: 20px;">';
        echo '<h3>主题初始化完成</h3>';
        echo '<p>您的 AUTH_TOKEN：<strong style="font-size: 18px; color: #0073aa;">' . esc_html($auth_token) . '</strong></p>';
        echo '<p>请保存此 token，填入 w.py 配置中用于 trans.php 接口认证。</p>';
        echo '</div>';
    }
});

// ============================================================
// Canonical URL 兜底（SEO 插件未输出 canonical 时）
// ============================================================
add_action('wp_head', function () {
    if (class_exists('RankMath') || defined('WPSEO_VERSION')) {
        return;
    }
    if (!function_exists('sonne_current_canonical_url')) {
        return;
    }
    $canonical = sonne_current_canonical_url();
    if ($canonical) {
        echo '<link rel="canonical" href="' . esc_url($canonical) . '" />' . "\n";
    }
}, 1);

// ============================================================
// Rank Math 输出规范化：站点语言/OG 类型/作者名/缺省分享图
// 由 header.php 在缓冲 wp_head 之后调用。
// ============================================================
function sonne_normalize_head_meta($head) {
    if (!is_string($head) || $head === '') {
        return $head;
    }

    // Rank Math inherits the zh_CN site locale; the site ships in US English.
    $head = preg_replace(
        '/<meta property="og:locale" content="[^"]*"\s*\/?>/',
        '<meta property="og:locale" content="en_US" />',
        $head
    );

    // Rank Math marks nearly every page as "article"; only posts really are.
    if (!is_singular('post')) {
        $head = preg_replace(
            '/<meta property="og:type" content="article"\s*\/?>/',
            '<meta property="og:type" content="website" />',
            $head
        );
    }

    // Never expose the WordPress login in the social byline.
    $head = preg_replace(
        '/<meta name="twitter:data1" content="jewels923"\s*\/?>/',
        '<meta name="twitter:data1" content="SONNE Engineering" />',
        $head
    );

    if (strpos($head, 'property="og:image"') === false) {
        $contact = require get_stylesheet_directory() . '/template-parts/data/site-contact.php';
        $image = $contact['default_og_image'];
        $head .= '<meta property="og:image" content="' . esc_url($image['url']) . '" />' . "\n";
        $head .= '<meta property="og:image:width" content="' . esc_attr($image['width']) . '" />' . "\n";
        $head .= '<meta property="og:image:height" content="' . esc_attr($image['height']) . '" />' . "\n";
        $head .= '<meta property="og:image:alt" content="' . esc_attr($image['alt']) . '" />' . "\n";
        if (strpos($head, 'name="twitter:card"') === false) {
            $head .= '<meta name="twitter:card" content="summary_large_image" />' . "\n";
        }
        $head .= '<meta name="twitter:image" content="' . esc_url($image['url']) . '" />' . "\n";
    }

    return $head;
}

// ============================================================
// 索引策略：topic 归档与 thank-you 不索引，也不进 sitemap
// ============================================================
function sonne_is_noindex_view() {
    return is_page('thank-you') || is_category();
}

add_filter('rank_math/frontend/robots', function ($robots) {
    if (!sonne_is_noindex_view()) {
        return $robots;
    }
    $robots['index'] = 'noindex';
    $robots['follow'] = 'follow';
    return $robots;
});

// 整类排除 category 分类法：sitemap 索引里也不会再列出 category-sitemap.xml
add_filter('rank_math/sitemap/exclude_taxonomy', function ($exclude, $taxonomy) {
    return $taxonomy === 'category' ? true : $exclude;
}, 10, 2);

add_filter('rank_math/sitemap/entry', function ($url, $type = '', $object = null) {
    // Rank Math 的 post provider 传入的是 stdClass（DB 原始行），不是 WP_Post，
    // 因此这里用属性存在性判断而不是 instanceof。
    if ($type === 'term' && isset($object->taxonomy) && $object->taxonomy === 'category') {
        return false;
    }
    if ($type === 'post' && isset($object->post_name) && $object->post_name === 'thank-you') {
        return false;
    }
    return $url;
}, 10, 3);

// Rank Math 把 sitemap 缓存成磁盘文件，REST 发布不会触发失效，新页面会缺席 sitemap 直到手动清缓存。
add_action('save_post', function ($post_id, $post, $update) {
    if (!$post instanceof WP_Post || 'publish' !== $post->post_status) {
        return;
    }
    if (!class_exists('RankMath\Sitemap\Cache')) {
        return;
    }
    $cache = new RankMath\Sitemap\Cache();
    $cache->invalidate_storage();
}, 20, 3);

// ============================================================
// Rank Math JSON-LD：站点与页面实体的唯一输出者
// ============================================================
function sonne_rank_math_organization_schema($contact) {
    $home = home_url('/');
    return array(
        '@type' => 'Organization',
        '@id' => $home . '#organization',
        'name' => $contact['brand_name'],
        'alternateName' => $contact['company_name'],
        'url' => $home,
        'email' => $contact['email'],
        'telephone' => $contact['phone'],
        'foundingDate' => $contact['founding_date'],
        'address' => array(
            '@type' => 'PostalAddress',
            'streetAddress' => $contact['address_street'],
            'addressLocality' => $contact['address_locality'],
            'addressRegion' => $contact['address_region'],
            'addressCountry' => $contact['address_country'],
        ),
        'logo' => array(
            '@type' => 'ImageObject',
            '@id' => $contact['logo_url'] . '#logo',
            'url' => $contact['logo_url'],
        ),
    );
}

function sonne_rank_math_repoint_person_refs($value, $legacy_ids, $organization_id) {
    if (!is_array($value)) {
        return $value;
    }
    if (isset($value['@id']) && is_string($value['@id']) && in_array($value['@id'], $legacy_ids, true)) {
        $value['@id'] = $organization_id;
        unset($value['name'], $value['url'], $value['image'], $value['sameAs']);
    }
    foreach ($value as $key => $item) {
        $value[$key] = sonne_rank_math_repoint_person_refs($item, $legacy_ids, $organization_id);
    }
    return $value;
}

function sonne_filter_rank_math_json_ld($data) {
    if (!is_array($data) || empty($data)) {
        return $data;
    }

    $contact = require get_stylesheet_directory() . '/template-parts/data/site-contact.php';
    $home = home_url('/');
    $organization_id = $home . '#organization';
    $legacy_ids = array($home . '#person');
    $keep_article = is_singular('post');
    // Rank Math passes a keyed entity map here and wraps it into @graph afterwards.
    $is_graph = isset($data['@graph']) && is_array($data['@graph']);
    $nodes = $is_graph ? $data['@graph'] : $data;
    $filtered = array();
    $organization_added = false;

    foreach ($nodes as $key => $node) {
        if (!is_array($node) || empty($node['@type'])) {
            $filtered[$key] = $node;
            continue;
        }
        $types = (array) $node['@type'];
        $is_organization = in_array('Organization', $types, true);
        $is_person = in_array('Person', $types, true);
        $is_article = in_array('Article', $types, true) || in_array('BlogPosting', $types, true);

        if ($is_person && !$is_organization) {
            if (!empty($node['@id']) && is_string($node['@id'])) {
                $legacy_ids[] = $node['@id'];
            }
            continue;
        }
        if ($is_article && !$keep_article) {
            continue;
        }
        if ($is_organization) {
            $filtered[$key] = sonne_rank_math_organization_schema($contact);
            $organization_added = true;
            continue;
        }
        if (in_array('WebSite', $types, true)) {
            $node['name'] = $contact['brand_name'];
            $node['publisher'] = array('@id' => $organization_id);
        }
        if ($is_article) {
            $node['author'] = array('@id' => $organization_id);
            $node['publisher'] = array('@id' => $organization_id);
        }
        $filtered[$key] = $node;
    }

    if (!$organization_added) {
        $key = isset($filtered['publisher']) ? 'organization' : 'publisher';
        $filtered[$key] = sonne_rank_math_organization_schema($contact);
    }

    $filtered = sonne_rank_math_repoint_person_refs(
        $filtered,
        array_values(array_unique($legacy_ids)),
        $organization_id
    );

    foreach ($filtered as &$node) {
        if (is_array($node) && isset($node['inLanguage'])) {
            $node['inLanguage'] = 'en-US';
        }
    }
    unset($node);

    if ($is_graph) {
        $data['@graph'] = array_values($filtered);
        return $data;
    }
    return $filtered;
}
add_filter('rank_math/json_ld', 'sonne_filter_rank_math_json_ld', 100);

// Rank Math runs wp_kses_post_deep after the filter, which re-encodes "&" as "&amp;".
function sonne_rank_math_json_ld_buffer_start() {
    ob_start();
}

function sonne_rank_math_json_ld_buffer_end() {
    $output = ob_get_clean();
    if (!is_string($output) || $output === '') {
        return;
    }
    $cleaned = preg_replace_callback(
        '#(<script type="application/ld\+json" class="rank-math-schema[^"]*">)(.*?)(</script>)#s',
        function ($matches) {
            return $matches[1]
                . str_replace(array('&amp;', '&#038;', '&#38;'), '&', $matches[2])
                . $matches[3];
        },
        $output
    );
    echo $cleaned === null ? $output : $cleaned;
}
add_action('rank_math/head', 'sonne_rank_math_json_ld_buffer_start', 89);
add_action('rank_math/head', 'sonne_rank_math_json_ld_buffer_end', 91);

// ============================================================
// FAQPage：从可见 FAQ 折叠块生成，已有内联 schema 的页面不重复输出
// ============================================================
function sonne_faq_clean_text($html, $texturize = true) {
    $html = (string) $html;
    $html = preg_replace('#<(script|style)\b[^>]*>.*?</\1>#is', ' ', $html);
    $html = preg_replace('#<br\s*/?>#i', ' ', $html);
    $html = preg_replace('#</?(?:p|div|li|ul|ol|h[1-6]|summary|details|section)\b[^>]*>#i', ' ', $html);
    $text = html_entity_decode(wp_strip_all_tags($html), ENT_QUOTES | ENT_HTML5, 'UTF-8');
    $text = preg_replace('/[\s\x{00A0}\x{2007}\x{202F}\x{FEFF}]+/u', ' ', $text);
    if (!is_string($text)) {
        $text = wp_strip_all_tags($html);
    }
    if ($texturize) {
        // 正文经 the_content 的 wptexturize 渲染，这里同步；它返回的是 HTML 实体，需再解码一次。
        $text = html_entity_decode(wptexturize($text), ENT_QUOTES | ENT_HTML5, 'UTF-8');
    }
    return trim($text);
}

function sonne_faq_pairs_from_html($html) {
    $html = (string) $html;
    if ('' === $html || false === stripos($html, '<details')) {
        return array();
    }
    if (!preg_match_all('#<details\b[^>]*>(.*?)</details>#is', $html, $matches)) {
        return array();
    }
    if (preg_match_all('#<details\b#i', $html) !== count($matches[1])) {
        return array();
    }
    $pairs = array();
    foreach ($matches[1] as $block) {
        if (false !== stripos($block, '<details')) {
            continue;
        }
        if (!preg_match('#<summary\b[^>]*>(.*?)</summary>(.*)$#is', $block, $parts)) {
            continue;
        }
        $q = sonne_faq_clean_text($parts[1]);
        $a = sonne_faq_clean_text($parts[2]);
        if ('' !== $q && '' !== $a) {
            $pairs[] = array('q' => $q, 'a' => $a);
        }
    }
    return count($pairs) >= 2 ? $pairs : array();
}

function sonne_faq_pairs_from_config($faqs) {
    $pairs = array();
    foreach ((array) $faqs as $faq) {
        if (!is_array($faq) || !isset($faq['q'], $faq['a'])) {
            continue;
        }
        // 归档页由 home.php 用 esc_html 渲染，不经过 wptexturize。
        $q = sonne_faq_clean_text($faq['q'], false);
        $a = sonne_faq_clean_text($faq['a'], false);
        if ('' !== $q && '' !== $a) {
            $pairs[] = array('q' => $q, 'a' => $a);
        }
    }
    return count($pairs) >= 2 ? $pairs : array();
}

function sonne_faq_has_schema($post_id, $content = null) {
    if (null !== $content && preg_match('#"@type"\s*:\s*"FAQPage"#', (string) $content)) {
        return true;
    }
    if (null !== $content && function_exists('has_block') && has_block('rank-math/faq-block', $post_id)) {
        return true;
    }
    foreach ((array) get_post_meta($post_id) as $key => $values) {
        if (0 === strpos((string) $key, 'rank_math_schema')) {
            $blob = wp_json_encode($values);
            if (is_string($blob) && false !== stripos($blob, 'FAQPage')) {
                return true;
            }
        }
    }
    return false;
}

function sonne_faq_schema_output() {
    if (is_admin() || is_feed() || is_preview() || is_404() || is_embed() || is_customize_preview()
        || (function_exists('wp_doing_ajax') && wp_doing_ajax())
        || (defined('REST_REQUEST') && REST_REQUEST) || is_paged()) {
        return;
    }

    $pairs = array();
    $url = '';
    if (is_singular('page')) {
        $post = get_queried_object();
        if (!($post instanceof WP_Post) || post_password_required($post)) {
            return;
        }
        if (sonne_faq_has_schema($post->ID, $post->post_content)) {
            return;
        }
        $pairs = sonne_faq_pairs_from_html(strip_shortcodes($post->post_content));
        $url = get_permalink($post);
    } elseif (is_home()) {
        $page_id = (int) get_option('page_for_posts');
        if (!$page_id || sonne_faq_has_schema($page_id, get_post_field('post_content', $page_id))) {
            return;
        }
        $config = function_exists('sonne_insights_config') ? sonne_insights_config() : array();
        $pairs = sonne_faq_pairs_from_config(isset($config['faqs']) ? $config['faqs'] : array());
        $url = get_permalink($page_id);
    } else {
        return;
    }

    if (count($pairs) < 2 || !$url) {
        return;
    }

    $main = array();
    foreach ($pairs as $pair) {
        $main[] = array(
            '@type' => 'Question',
            'name' => $pair['q'],
            'acceptedAnswer' => array('@type' => 'Answer', 'text' => $pair['a']),
        );
    }
    $json = wp_json_encode(array(
        '@context' => 'https://schema.org',
        '@type' => 'FAQPage',
        '@id' => $url . '#faq',
        'mainEntity' => $main,
    ), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_HEX_TAG | JSON_HEX_AMP);
    if (is_string($json) && '' !== $json) {
        echo '<script type="application/ld+json" class="sonne-faq-schema">' . $json . "</script>\n";
    }
}
add_action('wp_head', 'sonne_faq_schema_output', 20);

// ============================================================
// 301 重定向映射（改名页面时在这里添加）
// ============================================================
add_action('template_redirect', function () {
    $path = untrailingslashit(wp_parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
    $map = [
        // TODO: '/old-slug' => '/new-slug/',
    ];
    if (isset($map[$path])) {
        wp_redirect(home_url($map[$path]), 301);
        exit;
    }
}, 1);
