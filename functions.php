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

function child_theme_enqueue_assets() {
    // 父主题样式
    wp_enqueue_style('generate-style');

    // 主设计系统 main.css
    if (file_exists(get_stylesheet_directory() . '/main.css')) {
        wp_enqueue_style(
            'child-theme-main-css',
            get_stylesheet_directory_uri() . '/main.css',
            array('generate-style'),
            child_theme_asset_version('main.css')
        );
    }

    // SONNE shared tokens and chrome, loaded after the legacy design system.
    if (file_exists(get_stylesheet_directory() . '/sonne.css')) {
        wp_enqueue_style(
            'child-theme-sonne-css',
            get_stylesheet_directory_uri() . '/sonne.css',
            array('child-theme-main-css'),
            child_theme_asset_version('sonne.css')
        );
    }

    // SONNE Insights blog styles
    if (is_home() || is_category() || is_archive() || is_singular('post') || is_page('resources')) {
        if (file_exists(get_stylesheet_directory() . '/assets/css/sonne-insights.css')) {
            wp_enqueue_style(
                'sonne-insights',
                get_stylesheet_directory_uri() . '/assets/css/sonne-insights.css',
                array('child-theme-sonne-css'),
                child_theme_asset_version('assets/css/sonne-insights.css')
            );
        }
    }

    // Lenis 平滑滚动
    wp_enqueue_script('lenis', 'https://unpkg.com/lenis@1.1.20/dist/lenis.min.js', array(), '1.1.20', true);

    // GSAP + ScrollTrigger
    wp_enqueue_script('gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true);
    wp_enqueue_script('gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array('gsap'), '3.12.5', true);

    // 主动画脚本 main.js
    if (file_exists(get_stylesheet_directory() . '/main.js')) {
        wp_enqueue_script(
            'child-theme-main-js',
            get_stylesheet_directory_uri() . '/main.js',
            array('lenis', 'gsap', 'gsap-scrolltrigger'),
            child_theme_asset_version('main.js') ?: '1.0.0',
            true
        );
    }

    // 页头行为脚本（可选）
    if (file_exists(get_stylesheet_directory() . '/assets/site-header.js')) {
        wp_enqueue_script(
            'child-theme-site-header',
            get_stylesheet_directory_uri() . '/assets/site-header.js',
            array(),
            child_theme_asset_version('assets/site-header.js'),
            true
        );
    }
}
add_action('wp_enqueue_scripts', 'child_theme_enqueue_assets');

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
