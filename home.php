<?php
/**
 * SONNE Insights archive — rendered as the posts page.
 */
get_header();
get_template_part('template-parts/header');

$config = function_exists('sonne_insights_config') ? sonne_insights_config() : array();
$page = isset($config['page']) ? $config['page'] : array();
$faqs = isset($config['faqs']) ? $config['faqs'] : array();
$topics = function_exists('sonne_insight_topics') ? sonne_insight_topics() : array();
$h1 = isset($page['h1']) ? $page['h1'] : 'RF Engineering Guides for Buyers and Designers';
$insights_url = function_exists('sonne_insights_url') ? sonne_insights_url() : home_url('/resources/insights/');
$crumbs = array(
    array('name' => 'Home', 'url' => home_url('/')),
    array('name' => 'Resources', 'url' => home_url('/resources/')),
    array('name' => 'Insights', 'url' => $insights_url),
);
?>
<main id="main-content" class="sn-insights">
    <section class="sn-hero sn-insights-hero">
        <div class="sn-container">
            <?php echo sonne_insight_breadcrumbs($crumbs); ?>
            <p class="sn-insights-hero__eyebrow">Insights</p>
            <h1><?php echo esc_html($h1); ?></h1>
            <p class="sn-insights-hero__lede">Practical guides for RF, waveguide, combiner and enclosure projects. Start with the task in front of you, then move to the product page or a reviewable RFQ.</p>
            <div class="sn-insights-hero__actions">
                <a class="sn-btn sn-btn--primary" href="#topics">Browse Guide Topics</a>
                <a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Start a Custom RFQ</a>
            </div>
        </div>
    </section>

    <section class="sn-section" id="topics">
        <div class="sn-container">
            <header class="sn-section-head">
                <p class="sn-eyebrow">Content taxonomy</p>
                <h2>Browse Guides by Engineering Task</h2>
                <p>Use these six routes to find the guide that matches the task in front of you.</p>
            </header>
            <div class="sn-topic-grid">
                <?php foreach ($topics as $index => $topic) : ?>
                    <a class="sn-topic-card" href="<?php echo esc_url(sonne_topic_url($topic['slug'])); ?>">
                        <span class="sn-topic-card__index"><?php echo esc_html(str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT)); ?></span>
                        <h3><?php echo esc_html($topic['name']); ?></h3>
                        <p><?php echo esc_html($topic['description']); ?></p>
                        <span class="sn-topic-card__count"><?php echo esc_html(sonne_guide_count(sonne_topic_count($topic['slug']))); ?></span>
                    </a>
                <?php endforeach; ?>
            </div>
        </div>
    </section>

    <section class="sn-section sn-section--muted">
        <div class="sn-container">
            <header class="sn-section-head">
                <p class="sn-eyebrow">Latest</p>
                <h2>Latest Engineering Guides</h2>
                <p>Newest first. Use the topic routes above when you already know the engineering task.</p>
            </header>
            <?php if (have_posts()) : ?>
                <div class="sn-post-grid">
                    <?php while (have_posts()) : the_post(); ?>
                        <?php echo sonne_insight_post_card(get_the_ID()); ?>
                    <?php endwhile; ?>
                </div>
                <?php
                $links = paginate_links(array(
                    'type' => 'array',
                    'prev_text' => 'Previous',
                    'next_text' => 'Next',
                ));
                if ($links) :
                ?>
                    <nav class="sn-pagination" aria-label="Insights pagination">
                        <?php foreach ($links as $link) : ?>
                            <?php echo $link; ?>
                        <?php endforeach; ?>
                    </nav>
                <?php endif; ?>
            <?php else : ?>
                <div class="sn-empty">
                    <p class="sn-eyebrow">In preparation</p>
                    <h3>The first SONNE guides are in preparation.</h3>
                    <p>The six topic routes are already open. Product pages and engineering evidence cover the same selection inputs in the meantime.</p>
                    <div class="sn-empty__links">
                        <a class="sn-btn sn-btn--primary" href="<?php echo esc_url(home_url('/products/')); ?>">Browse Products</a>
                        <a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(home_url('/engineering/')); ?>">Review Engineering</a>
                        <a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Start a Custom RFQ</a>
                    </div>
                </div>
            <?php endif; ?>
        </div>
    </section>

    <section class="sn-section">
        <div class="sn-container">
            <header class="sn-section-head">
                <p class="sn-eyebrow">From guide to review</p>
                <h2>Move from Selection Logic to RFQ Inputs</h2>
            </header>
            <div class="sn-path-grid">
                <article class="sn-path-card"><span class="sn-path-card__index">01</span><h3>Learn the topology</h3><p>Compare product families and the terms used in a specification.</p><a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(home_url('/products/')); ?>">Explore Products</a></article>
                <article class="sn-path-card"><span class="sn-path-card__index">02</span><h3>Prepare the inputs</h3><p>Check how design, manufacturing and test evidence are handled.</p><a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(home_url('/engineering/')); ?>">Review Engineering</a></article>
                <article class="sn-path-card"><span class="sn-path-card__index">03</span><h3>Submit the project</h3><p>Send a band plan, specification or drawing for engineering review.</p><a class="sn-btn sn-btn--secondary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Start a Custom RFQ</a></article>
            </div>
        </div>
    </section>

    <section class="sn-section sn-section--muted">
        <div class="sn-container">
            <header class="sn-section-head">
                <p class="sn-eyebrow">Reading checklist</p>
                <h2>What to Check in Any RF Guide</h2>
            </header>
            <div class="sn-steps">
                <article class="sn-path-card"><span class="sn-path-card__index">01</span><h3>Comparison criteria</h3><p>Frequency, bandwidth, topology, insertion loss, rejection or isolation, power and PIM.</p></article>
                <article class="sn-path-card"><span class="sn-path-card__index">02</span><h3>Measurement conditions</h3><p>Test setup, calibration, frequency range, limits and sample or lot identity.</p></article>
                <article class="sn-path-card"><span class="sn-path-card__index">03</span><h3>RFQ inputs</h3><p>The known inputs, the missing inputs and the next engineering step.</p></article>
            </div>
        </div>
    </section>

    <section class="sn-section">
        <div class="sn-container">
            <header class="sn-section-head">
                <p class="sn-eyebrow">FAQ</p>
                <h2>RF Engineering Guide FAQs</h2>
            </header>
            <?php foreach ($faqs as $faq) : ?>
                <details class="sn-faq">
                    <summary><?php echo esc_html($faq['q']); ?></summary>
                    <div class="sn-faq__answer"><p><?php echo esc_html($faq['a']); ?></p></div>
                </details>
            <?php endforeach; ?>
        </div>
    </section>

    <section class="sn-section sn-section--muted">
        <div class="sn-container">
            <div class="sn-cta">
                <h2>Have a specification or drawing?</h2>
                <p>Send the inputs you have. Engineering can identify the gaps. A complete RFQ receives initial feedback in about 24 hours; it is not an automatic quotation.</p>
                <a class="sn-btn sn-btn--primary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Start a Custom RFQ</a>
            </div>
        </div>
    </section>
    <?php
    echo sonne_schema_json(sonne_breadcrumb_schema($crumbs));
    ?>
</main>
<?php
get_template_part('template-parts/footer');
get_footer();
