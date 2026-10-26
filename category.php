<?php
/**
 * SONNE Insights topic archive.
 */
get_header();
get_template_part('template-parts/header');

$term = get_queried_object();
$name = single_cat_title('', false);
$description = $term ? category_description($term) : '';
$count = $term ? (int) $term->count : 0;
$term_url = $term ? get_category_link($term) : sonne_insights_url();
$crumbs = array(
    array('name' => 'Home', 'url' => home_url('/')),
    array('name' => 'Resources', 'url' => home_url('/resources/')),
    array('name' => 'Insights', 'url' => sonne_insights_url()),
    array('name' => $name, 'url' => $term_url),
);
?>
<main id="main-content" class="sn-insights sn-insights--category">
    <section class="sn-hero sn-insights-hero">
        <div class="sn-container">
            <?php echo sonne_insight_breadcrumbs($crumbs); ?>
            <p class="sn-insights-hero__eyebrow">Topic</p>
            <h1><?php echo esc_html($name); ?></h1>
            <?php if ($description) : ?>
                <div class="sn-insights-hero__lede"><?php echo wp_kses_post($description); ?></div>
            <?php endif; ?>
            <p class="sn-insights-hero__lede"><?php echo esc_html(sonne_guide_count($count)); ?></p>
            <div class="sn-insights-hero__actions">
                <a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(sonne_insights_url()); ?>">All Insights</a>
            </div>
        </div>
    </section>

    <section class="sn-section">
        <div class="sn-container">
            <?php if (have_posts()) : ?>
                <div class="sn-post-grid">
                    <?php while (have_posts()) : the_post(); ?>
                        <?php echo sonne_insight_post_card(get_the_ID()); ?>
                    <?php endwhile; ?>
                </div>
                <?php
                $links = paginate_links(array('type' => 'array', 'prev_text' => 'Previous', 'next_text' => 'Next'));
                if ($links) :
                ?>
                    <nav class="sn-pagination" aria-label="Topic pagination">
                        <?php foreach ($links as $link) : ?>
                            <?php echo $link; ?>
                        <?php endforeach; ?>
                    </nav>
                <?php endif; ?>
            <?php else : ?>
                <div class="sn-empty">
                    <p class="sn-eyebrow">In preparation</p>
                    <h2>No guides in this topic yet.</h2>
                    <p>Browse all topics, start from the product family that matches your project, or send a specification for review.</p>
                    <div class="sn-empty__links">
                        <a class="sn-btn sn-btn--primary" href="<?php echo esc_url(sonne_insights_url()); ?>">All Insights</a>
                        <a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(home_url('/products/')); ?>">Browse Products</a>
                        <a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Start a Custom RFQ</a>
                    </div>
                </div>
            <?php endif; ?>
        </div>
    </section>
    <?php
    $schema = array(
        '@context' => 'https://schema.org',
        '@type' => 'CollectionPage',
        'name' => $name,
        'description' => wp_strip_all_tags($description),
        'url' => $term_url,
    );
    echo sonne_schema_json($schema);
    echo sonne_schema_json(sonne_breadcrumb_schema($crumbs));
    ?>
</main>
<?php
get_template_part('template-parts/footer');
get_footer();
