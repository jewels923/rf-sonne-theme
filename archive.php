<?php
/**
 * Generic SONNE archive fallback for tags, dates and other taxonomies.
 */
get_header();
get_template_part('template-parts/header');

$title = wp_strip_all_tags(get_the_archive_title());
$description = get_the_archive_description();
$crumbs = array(
    array('name' => 'Home', 'url' => home_url('/')),
    array('name' => 'Resources', 'url' => home_url('/resources/')),
    array('name' => 'Insights', 'url' => sonne_insights_url()),
    array('name' => $title, 'url' => get_pagenum_link(1)),
);
?>
<main id="main-content" class="sn-insights sn-insights--archive">
    <section class="sn-hero sn-insights-hero">
        <div class="sn-container">
            <?php echo sonne_insight_breadcrumbs($crumbs); ?>
            <p class="sn-insights-hero__eyebrow">Archive</p>
            <h1><?php echo esc_html($title); ?></h1>
            <?php if ($description) : ?>
                <div class="sn-insights-hero__lede"><?php echo wp_kses_post($description); ?></div>
            <?php endif; ?>
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
                    <nav class="sn-pagination" aria-label="Archive pagination">
                        <?php foreach ($links as $link) : ?>
                            <?php echo $link; ?>
                        <?php endforeach; ?>
                    </nav>
                <?php endif; ?>
            <?php else : ?>
                <div class="sn-empty">
                    <p class="sn-eyebrow">In preparation</p>
                    <h2>No posts in this archive yet.</h2>
                    <p>Browse all insights or start from the product family that matches your project.</p>
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
    echo sonne_schema_json(sonne_breadcrumb_schema($crumbs));
    ?>
</main>
<?php
get_template_part('template-parts/footer');
get_footer();
