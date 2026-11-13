<?php
$contact = require __DIR__ . '/data/site-contact.php';
$footer_groups = require __DIR__ . '/data/footer-groups.php';
?>

<footer class="site-footer">
    <div class="container-xl sn-container">
        <div class="site-footer__top">
            <div class="site-footer__brand">
                <a class="site-footer__brand-logo-link" href="<?php echo esc_url(home_url('/')); ?>" aria-label="<?php echo esc_attr($contact['brand_name']); ?> home">
                    <img
                        src="<?php echo esc_url($contact['logo_url']); ?>"
                        srcset="<?php echo esc_url($contact['logo_small_url']); ?> 300w, <?php echo esc_url($contact['logo_url']); ?> 381w"
                        sizes="180px"
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
            <a class="site-footer__contact-detail site-footer__contact-detail--email" href="<?php echo esc_url('mailto:' . $contact['email']); ?>">
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
                    <rect x="3" y="5.5" width="18" height="13" rx="2" stroke="currentColor" stroke-width="1.6"/>
                    <path d="m3.8 7 7.2 5.1a2 2 0 0 0 2 0L20.2 7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                </svg>
                <span>
                    <span class="site-footer__contact-label">Email</span>
                    <span class="site-footer__contact-value"><?php echo esc_html($contact['email']); ?></span>
                </span>
            </a>
            <a class="site-footer__contact-detail site-footer__contact-detail--whatsapp" href="<?php echo esc_url('https://wa.me/' . $contact['whatsapp_href']); ?>" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/>
                </svg>
                <span>
                    <span class="site-footer__contact-label">WhatsApp</span>
                    <span class="site-footer__contact-value">Chat on WhatsApp</span>
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
