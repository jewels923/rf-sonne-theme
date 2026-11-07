<?php
/**
 * SONNE site search results.
 */
get_header();
get_template_part('template-parts/header');

$search_query = get_search_query(false);
$found_posts = isset($GLOBALS['wp_query']->found_posts) ? (int) $GLOBALS['wp_query']->found_posts : 0;
$crumbs = array(
    array('name' => 'Home', 'url' => home_url('/')),
    array('name' => 'Search', 'url' => get_search_link($search_query)),
);
?>
<main id="main-content" class="sn-insights sn-insights--search">
    <section class="sn-hero sn-insights-hero">
        <div class="sn-container">
            <?php echo sonne_insight_breadcrumbs($crumbs); ?>
            <p class="sn-insights-hero__eyebrow">Search</p>
            <?php if ('' !== $search_query) : ?>
                <h1><?php echo esc_html(sprintf('Results for "%s"', $search_query)); ?></h1>
                <p class="sn-insights-hero__lede">
                    <?php echo esc_html(sprintf(_n('%s match across products, pages and insights.', '%s matches across products, pages and insights.', $found_posts), number_format_i18n($found_posts))); ?>
                </p>
            <?php else : ?>
                <h1>Search SONNE</h1>
                <p class="sn-insights-hero__lede">Enter a product, application or document name.</p>
            <?php endif; ?>
            <form class="sn-search-form" role="search" method="get" action="<?php echo esc_url(home_url('/')); ?>">
                <label class="screen-reader-text" for="sn-search-input">Search the SONNE website</label>
                <div class="sn-search-form__row">
                    <input class="sn-search-form__input" id="sn-search-input" type="search" name="s" value="<?php echo esc_attr($search_query); ?>" placeholder="Product, application or document">
                    <button class="sn-search-form__button" type="submit">Search</button>
                </div>
            </form>
        </div>
    </section>

    <section class="sn-section">
        <div class="sn-container">
            <?php if (have_posts()) : ?>
                <div class="sn-search-results">
                    <?php while (have_posts()) : the_post(); ?>
                        <?php
                        $result_type = get_post_type();
                        $type_label = 'post' === $result_type ? 'Insight' : ('page' === $result_type ? 'Page' : ucfirst($result_type));
                        $result_excerpt = wp_strip_all_tags(get_the_excerpt());
                        if ('' === trim($result_excerpt)) {
                            $result_excerpt = wp_trim_words(wp_strip_all_tags(get_the_content()), 32);
                        }
                        ?>
                        <article class="sn-search-result">
                            <p class="sn-search-result__type"><?php echo esc_html($type_label); ?></p>
                            <h2 class="sn-search-result__title">
                                <a href="<?php echo esc_url(get_permalink()); ?>"><?php echo esc_html(get_the_title()); ?></a>
                            </h2>
                            <?php if ('' !== $result_excerpt) : ?>
                                <p class="sn-search-result__excerpt"><?php echo esc_html($result_excerpt); ?></p>
                            <?php endif; ?>
                        </article>
                    <?php endwhile; ?>
                </div>
                <?php
                $links = paginate_links(array('type' => 'array', 'prev_text' => 'Previous', 'next_text' => 'Next'));
                if ($links) :
                ?>
                    <nav class="sn-pagination" aria-label="Search results pagination">
                        <?php foreach ($links as $link) : ?>
                            <?php echo $link; ?>
                        <?php endforeach; ?>
                    </nav>
                <?php endif; ?>
            <?php else : ?>
                <div class="sn-empty">
                    <p class="sn-eyebrow">No matches</p>
                    <?php if ('' !== $search_query) : ?>
                        <h2>Nothing matched "<?php echo esc_html($search_query); ?>".</h2>
                    <?php else : ?>
                        <h2>Enter a search term to begin.</h2>
                    <?php endif; ?>
                    <p>Try a product family, an application or a document name. You can also send the requirement directly and an engineer will review it.</p>
                    <div class="sn-empty__links">
                        <a class="sn-btn sn-btn--primary" href="<?php echo esc_url(home_url('/products/')); ?>">Browse Products</a>
                        <a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Start a Custom RFQ</a>
                        <a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(sonne_insights_url()); ?>">All Insights</a>
                    </div>
                </div>
            <?php endif; ?>
        </div>
    </section>
</main>
<?php
get_template_part('template-parts/footer');
get_footer();