<?php
/**
 * SONNE Insights helpers: config, cards, TOC, schema and canonical URLs.
 */

function sonne_insights_config() {
    static $config = null;
    if (null === $config) {
        $path = get_stylesheet_directory() . '/inc/data/insights.json';
        $raw = is_readable($path) ? file_get_contents($path) : '';
        $decoded = $raw ? json_decode($raw, true) : null;
        $config = is_array($decoded) ? $decoded : array('page' => array(), 'hub' => array(), 'topics' => array(), 'faqs' => array());
    }
    return $config;
}

function sonne_insight_topics() {
    $config = sonne_insights_config();
    return array_values(array_filter(isset($config['topics']) ? $config['topics'] : array(), 'is_array'));
}

function sonne_topic_by_slug($slug) {
    foreach (sonne_insight_topics() as $topic) {
        if (isset($topic['slug']) && $topic['slug'] === $slug) {
            return $topic;
        }
    }
    return null;
}

function sonne_topic_count($slug) {
    $term = get_term_by('slug', $slug, 'category');
    return ($term && !is_wp_error($term)) ? (int) $term->count : 0;
}

function sonne_guide_count($count) {
    $count = (int) $count;
    return $count . ' ' . ($count === 1 ? 'guide' : 'guides');
}

function sonne_insights_url() {
    $page_id = (int) get_option('page_for_posts');
    return $page_id ? get_permalink($page_id) : home_url('/resources/insights/');
}

function sonne_topic_url($slug) {
    $term = get_term_by('slug', $slug, 'category');
    return ($term && !is_wp_error($term)) ? get_term_link($term) : sonne_insights_url();
}

function sonne_reading_time($post_id) {
    $content = wp_strip_all_tags((string) get_post_field('post_content', $post_id));
    $words = str_word_count($content);
    return max(1, (int) ceil($words / 200));
}

function sonne_insight_excerpt($post_id, $words = 28) {
    $excerpt = (string) get_post_field('post_excerpt', $post_id);
    if ('' === trim($excerpt)) {
        $excerpt = (string) get_post_field('post_content', $post_id);
    }
    $excerpt = wp_strip_all_tags(strip_shortcodes($excerpt));
    return wp_trim_words($excerpt, $words, '…');
}

function sonne_insight_post_card($post_id) {
    $post_id = (int) $post_id;
    $permalink = get_permalink($post_id);
    $title = get_the_title($post_id);
    $excerpt = sonne_insight_excerpt($post_id);
    $categories = get_the_category($post_id);
    $category = $categories ? $categories[0] : null;
    $show_category = $category && 'uncategorized' !== $category->slug;
    $image_id = get_post_thumbnail_id($post_id);
    $image_alt = $image_id ? (string) get_post_meta($image_id, '_wp_attachment_image_alt', true) : '';
    if ('' === $image_alt) {
        $image_alt = $title;
    }

    ob_start();
    ?>
    <article class="sn-post-card">
        <a class="sn-post-card__media<?php echo $image_id ? '' : ' sn-post-card__media--placeholder'; ?>" href="<?php echo esc_url($permalink); ?>"<?php echo $image_id ? '' : ' aria-hidden="true" tabindex="-1"'; ?>>
            <?php if ($image_id) : ?>
                <?php echo wp_get_attachment_image($image_id, 'sonne-insight-card', false, array('loading' => 'lazy', 'alt' => $image_alt)); ?>
            <?php else : ?>
                <span><?php echo esc_html($show_category ? $category->name : 'SONNE Insights'); ?></span>
            <?php endif; ?>
        </a>
        <div class="sn-post-card__body">
            <?php if ($show_category) : ?>
                <a class="sn-chip" href="<?php echo esc_url(get_category_link($category->term_id)); ?>"><?php echo esc_html($category->name); ?></a>
            <?php endif; ?>
            <h3 class="sn-post-card__title"><a href="<?php echo esc_url($permalink); ?>"><?php echo esc_html($title); ?></a></h3>
            <p class="sn-post-card__excerpt"><?php echo esc_html($excerpt); ?></p>
            <div class="sn-post-card__meta">
                <time datetime="<?php echo esc_attr(get_the_date('c', $post_id)); ?>"><?php echo esc_html(get_post_time('M j, Y', false, $post_id)); ?></time>
                <span><?php echo esc_html(sonne_reading_time($post_id)); ?> min read</span>
            </div>
        </div>
    </article>
    <?php
    return (string) ob_get_clean();
}

function sonne_insight_breadcrumbs($items) {
    ob_start();
    ?>
    <nav class="sn-breadcrumbs" aria-label="Breadcrumb">
        <ol>
            <?php foreach ($items as $index => $item) : ?>
                <li>
                    <?php if (!empty($item['url']) && $index < count($items) - 1) : ?>
                        <a href="<?php echo esc_url($item['url']); ?>"><?php echo esc_html($item['name']); ?></a>
                    <?php else : ?>
                        <span aria-current="page"><?php echo esc_html($item['name']); ?></span>
                    <?php endif; ?>
                </li>
            <?php endforeach; ?>
        </ol>
    </nav>
    <?php
    return (string) ob_get_clean();
}

function sonne_breadcrumb_schema($items) {
    $list = array();
    foreach (array_values($items) as $index => $item) {
        $entry = array('@type' => 'ListItem', 'position' => $index + 1, 'name' => $item['name']);
        if (!empty($item['url'])) {
            $entry['item'] = $item['url'];
        }
        $list[] = $entry;
    }
    return array('@context' => 'https://schema.org', '@type' => 'BreadcrumbList', 'itemListElement' => $list);
}

function sonne_schema_json($data) {
    return '<script type="application/ld+json">' . wp_json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . '</script>';
}

function sonne_insight_content_anchors($content) {
    if (!is_singular('post') || is_admin()) {
        return $content;
    }
    $used = array();
    return preg_replace_callback('/<h([23])([^>]*)>(.*?)<\/h\1>/is', function ($match) use (&$used) {
        if (preg_match('/\bid\s*=/i', $match[2])) {
            return $match[0];
        }
        $text = wp_strip_all_tags($match[3]);
        $base = sanitize_title($text);
        if ('' === $base) {
            $base = 'section';
        }
        $id = $base;
        $suffix = 2;
        while (isset($used[$id])) {
            $id = $base . '-' . $suffix;
            $suffix++;
        }
        $used[$id] = true;
        return '<h' . $match[1] . $match[2] . ' id="' . esc_attr($id) . '">' . $match[3] . '</h' . $match[1] . '>';
    }, $content);
}

function sonne_insight_toc_from_html($html) {
    if (!preg_match_all('/<h([23])\b[^>]*\bid="([^"]+)"[^>]*>(.*?)<\/h\1>/is', $html, $matches, PREG_SET_ORDER)) {
        return '';
    }
    $items = '';
    foreach ($matches as $match) {
        $level = (int) $match[1];
        $text = wp_strip_all_tags($match[3]);
        if ('' === trim($text)) {
            continue;
        }
        $items .= '<li class="sn-toc__item sn-toc__item--h' . $level . '"><a href="#' . esc_attr($match[2]) . '">' . esc_html($text) . '</a></li>';
    }
    return $items ? '<ul>' . $items . '</ul>' : '';
}

function sonne_insight_wrap_tables($content) {
    if (!is_singular('post') || is_admin()) {
        return $content;
    }
    return preg_replace_callback('/<table\b[^>]*>.*?<\/table>/is', function ($match) {
        return '<div class="sn-table-wrap" tabindex="0" role="region" aria-label="Data table">' . $match[0] . '</div>';
    }, $content);
}

function sonne_current_canonical_url() {
    if (is_front_page()) {
        return home_url('/');
    }
    if (is_singular()) {
        return get_permalink();
    }
    if (is_home()) {
        $page_id = (int) get_option('page_for_posts');
        return $page_id ? get_permalink($page_id) : home_url('/');
    }
    if (is_category()) {
        return get_category_link(get_queried_object_id());
    }
    if (is_author()) {
        return get_author_posts_url(get_queried_object_id());
    }
    if (is_archive()) {
        return get_pagenum_link(1);
    }
    return '';
}

add_action('after_setup_theme', function () {
    add_image_size('sonne-insight-card', 800, 450, true);
    add_image_size('sonne-insight-wide', 1600, 900, true);
});

add_filter('the_content', 'sonne_insight_content_anchors', 11);
add_filter('the_content', 'sonne_insight_wrap_tables', 12);

add_action('template_redirect', function () {
    if (is_author()) {
        wp_safe_redirect(home_url('/resources/insights/'), 301);
        exit;
    }
}, 1);
