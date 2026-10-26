<?php
/**
 * SONNE Insights article template: TOC, reading time, evidence CTA, related guides.
 */
get_header();
get_template_part('template-parts/header');

if (have_posts()) :
    while (have_posts()) : the_post();
        $post_id = get_the_ID();
        $raw_content = (string) get_post_field('post_content', $post_id);
        $rendered = apply_filters('the_content', $raw_content);
        $toc = sonne_insight_toc_from_html($rendered);
        $categories = get_the_category($post_id);
        $category = $categories ? $categories[0] : null;
        $show_category = $category && 'uncategorized' !== $category->slug;
        $image_id = get_post_thumbnail_id($post_id);
        $image_alt = $image_id ? (string) get_post_meta($image_id, '_wp_attachment_image_alt', true) : '';
        if ('' === $image_alt) {
            $image_alt = get_the_title();
        }
        $crumbs = array(
            array('name' => 'Home', 'url' => home_url('/')),
            array('name' => 'Resources', 'url' => home_url('/resources/')),
            array('name' => 'Insights', 'url' => sonne_insights_url()),
        );
        if ($show_category) {
            $crumbs[] = array('name' => $category->name, 'url' => get_category_link($category->term_id));
        }
        $crumbs[] = array('name' => get_the_title(), 'url' => get_permalink());
        ?>
        <main id="main-content" class="sn-insights sn-insights--post">
            <section class="sn-hero sn-insights-hero">
                <div class="sn-container">
                    <?php echo sonne_insight_breadcrumbs($crumbs); ?>
                    <?php if ($show_category) : ?>
                        <a class="sn-chip" href="<?php echo esc_url(get_category_link($category->term_id)); ?>"><?php echo esc_html($category->name); ?></a>
                    <?php endif; ?>
                    <h1><?php echo esc_html(get_the_title()); ?></h1>
                    <div class="sn-post-card__meta">
                        <time datetime="<?php echo esc_attr(get_the_date('c')); ?>"><?php echo esc_html(get_post_time('M j, Y')); ?></time>
                        <span><?php echo esc_html(sonne_reading_time($post_id)); ?> min read</span>
                        <span>SONNE Engineering</span>
                    </div>
                </div>
            </section>

            <section class="sn-section">
                <div class="sn-container sn-article-layout">
                    <article class="sn-article">
                        <?php if ($image_id) : ?>
                            <figure class="sn-article__hero-image">
                                <?php echo wp_get_attachment_image($image_id, 'sonne-insight-wide', false, array('loading' => 'eager', 'alt' => $image_alt)); ?>
                            </figure>
                        <?php endif; ?>
                        <?php if ($toc) : ?>
                            <details class="sn-toc sn-toc--mobile">
                                <summary class="sn-toc__label">On this page</summary>
                                <?php echo $toc; ?>
                            </details>
                        <?php endif; ?>
                        <div class="sn-article__body"><?php echo $rendered; ?></div>

                        <div class="sn-article__cta">
                            <h2>Have a band plan or drawing?</h2>
                            <p>Submit what you have for an initial engineering review. A complete RFQ can receive feedback in about 24 hours; it is not an automatic quotation.</p>
                            <a class="sn-btn sn-btn--primary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Request a Quote</a>
                        </div>

                        <?php
                        $related = get_posts(array(
                            'category__in' => wp_get_post_categories($post_id),
                            'post__not_in' => array($post_id),
                            'numberposts' => 3,
                            'post_status' => 'publish',
                        ));
                        if ($related) :
                        ?>
                            <section class="sn-related">
                                <header class="sn-section-head">
                                    <p class="sn-eyebrow">Keep reading</p>
                                    <h2>Related Guides</h2>
                                </header>
                                <div class="sn-post-grid">
                                    <?php foreach ($related as $related_post) : ?>
                                        <?php echo sonne_insight_post_card($related_post->ID); ?>
                                    <?php endforeach; ?>
                                </div>
                            </section>
                        <?php endif; ?>
                    </article>

                    <aside class="sn-article__aside">
                        <?php if ($toc) : ?>
                            <nav class="sn-toc" aria-label="On this page">
                                <p class="sn-toc__label">On this page</p>
                                <?php echo $toc; ?>
                            </nav>
                        <?php endif; ?>
                        <div class="sn-article__cta">
                            <h3>Need an engineering review?</h3>
                            <p>Send a band plan, specification or drawing. Engineering can identify the missing inputs.</p>
                            <a class="sn-btn sn-btn--primary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Request a Quote</a>
                        </div>
                    </aside>
                </div>
            </section>
            <?php
            $contact = require get_stylesheet_directory() . '/template-parts/data/site-contact.php';
            $schema = array(
                '@context' => 'https://schema.org',
                '@type' => 'BlogPosting',
                'headline' => get_the_title(),
                'description' => sonne_insight_excerpt($post_id, 40),
                'datePublished' => get_the_date('c'),
                'dateModified' => get_the_modified_date('c'),
                'mainEntityOfPage' => array('@type' => 'WebPage', '@id' => get_permalink()),
                'author' => array('@type' => 'Organization', 'name' => 'SONNE', 'url' => home_url('/')),
                'publisher' => array(
                    '@type' => 'Organization',
                    'name' => 'SONNE',
                    'url' => home_url('/'),
                    'logo' => array('@type' => 'ImageObject', 'url' => $contact['logo_url']),
                ),
            );
            if ($image_id) {
                $schema['image'] = array(wp_get_attachment_image_url($image_id, 'sonne-insight-wide'));
            }
            echo sonne_schema_json($schema);
            echo sonne_schema_json(sonne_breadcrumb_schema($crumbs));
            ?>
        </main>
        <?php
    endwhile;
endif;
get_template_part('template-parts/footer');
get_footer();
