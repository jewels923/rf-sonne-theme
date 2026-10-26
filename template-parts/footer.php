<?php
$contact = require __DIR__ . '/data/site-contact.php';
$footer_groups = require __DIR__ . '/data/footer-groups.php';
$organization_schema = array(
    '@context' => 'https://schema.org',
    '@graph' => array(
        array(
            '@type' => 'Organization',
            '@id' => home_url('/#organization'),
            'name' => $contact['company_name'],
            'url' => home_url('/'),
            'email' => $contact['email'],
            'telephone' => $contact['phone'],
            'address' => array(
                '@type' => 'PostalAddress',
                'streetAddress' => $contact['address_street'],
                'addressLocality' => $contact['address_locality'],
                'addressRegion' => $contact['address_region'],
                'addressCountry' => $contact['address_country'],
            ),
            'logo' => array(
                '@type' => 'ImageObject',
                'url' => $contact['logo_url'],
            ),
        ),
        array(
            '@type' => 'WPFooter',
            'copyrightYear' => date_i18n('Y'),
            'copyrightHolder' => array(
                '@id' => home_url('/#organization'),
            ),
        ),
    ),
);
?>

<footer class="site-footer">
    <script type="application/ld+json"><?php echo wp_json_encode($organization_schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE); ?></script>
    <div class="container-xl sn-container">
        <div class="site-footer__top">
            <div class="site-footer__brand">
                <a class="site-footer__brand-logo-link" href="<?php echo esc_url(home_url('/')); ?>" aria-label="<?php echo esc_attr($contact['brand_name']); ?> home">
                    <img
                        src="<?php echo esc_url($contact['logo_url']); ?>"
                        alt="<?php echo esc_attr($contact['logo_alt']); ?>"
                        class="site-footer__brand-logo"
                        width="381"
                        height="102"
                    >
                </a>
                <p class="site-footer__brand-copy">
                    Custom RF and microwave components, waveguide assemblies and precision enclosures for engineering-led projects.
                </p>
                <div class="site-footer__brand-actions">
                    <a class="sn-btn sn-btn--primary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Request a Quote</a>
                </div>
            </div>

            <div class="site-footer__menus">
                <?php foreach ($footer_groups as $group_title => $links) : ?>
                    <div class="site-footer__menu-group">
                        <p class="site-footer__menu-title"><?php echo esc_html($group_title); ?></p>
                        <ul class="site-footer__menu-list">
                            <?php foreach ($links as $link) : ?>
                                <li>
                                    <a href="<?php echo esc_url($link['url']); ?>">
                                        <?php echo esc_html($link['label']); ?>
                                    </a>
                                </li>
                            <?php endforeach; ?>
                        </ul>
                    </div>
                <?php endforeach; ?>

                <div class="site-footer__menu-group">
                    <p class="site-footer__menu-title">Contact</p>
                    <ul class="site-footer__menu-list site-footer__contact-list">
                        <li>
                            <a href="<?php echo esc_url('mailto:' . $contact['email']); ?>"><?php echo esc_html($contact['email']); ?></a>
                        </li>
                        <li><a href="<?php echo esc_url(home_url('/contact/')); ?>">Contact SONNE</a></li>
                        <li><a href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Request a Quote</a></li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="site-footer__contact-details">
            <a class="site-footer__contact-detail" href="tel:<?php echo esc_attr($contact['phone_href']); ?>">
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.58 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1 11.4 11.4 0 0 0 .58 3.6 1 1 0 0 1-.25 1z" fill="currentColor"/></svg>
                <span>
                    <span class="site-footer__contact-label">Telephone</span>
                    <span class="site-footer__contact-value"><?php echo esc_html($contact['phone']); ?></span>
                </span>
            </a>
            <div class="site-footer__contact-detail">
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z" fill="currentColor"/></svg>
                <span>
                    <span class="site-footer__contact-label">Manufacturing base</span>
                    <span class="site-footer__contact-value"><?php echo esc_html($contact['address']); ?></span>
                </span>
            </div>
        </div>

        <div class="site-footer__bottom">
            <p>&copy; <?php echo esc_html(date_i18n('Y')); ?> <?php echo esc_html($contact['company_name']); ?>. All rights reserved.</p>
            <div class="site-footer__bottom-links">
                <a href="<?php echo esc_url(home_url('/privacy-policy/')); ?>">Privacy Policy</a>
                <a href="<?php echo esc_url(home_url('/terms-of-service/')); ?>">Terms of Service</a>
                <a href="<?php echo esc_url(home_url('/sitemap/')); ?>">Sitemap</a>
            </div>
            <a href="#site-top" class="site-footer__back-top" aria-label="Back to top" data-back-top>
                <span class="site-footer__back-top-label">Back to top</span>
                <span class="site-footer__back-top-icon" aria-hidden="true"></span>
            </a>
        </div>
    </div>
</footer>

<script>
document.addEventListener('DOMContentLoaded', function () {
    var backTop = document.querySelector('[data-back-top]');
    if (!backTop) {
        return;
    }

    var footer = document.querySelector('.site-footer');
    var footerVisible = false;

    function toggleBackTop() {
        var shouldShow = window.scrollY > 400;
        if (footerVisible) {
            shouldShow = false;
        }
        backTop.classList.toggle('is-visible', shouldShow);
    }

    if (footer) {
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (entries) {
                footerVisible = entries[0].isIntersecting;
                toggleBackTop();
            }, { threshold: 0 }).observe(footer);
        }
    }

    window.addEventListener('scroll', toggleBackTop, { passive: true });
    toggleBackTop();

    backTop.addEventListener('click', function (event) {
        event.preventDefault();
        var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
});
</script>
