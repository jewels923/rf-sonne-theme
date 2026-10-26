<?php
$contact = require __DIR__ . '/data/site-contact.php';
$header_config = require __DIR__ . '/data/header-navigation.php';
$mega_menu_defaults = $header_config['mega_menu_defaults'];
$navigation = $header_config['navigation'];
?>

<div id="site-top" aria-hidden="true"></div>
<header class="site-header-shell">
    <div class="site-utility-bar">
        <div class="container-xl sn-container site-utility-bar__inner">
            <p class="site-utility-bar__message">Custom RF &amp; microwave components and precision enclosures.</p>
            <div class="site-utility-bar__links">
                <a href="tel:<?php echo esc_attr($contact['phone_href']); ?>">
                    <?php echo esc_html($contact['phone']); ?>
                </a>
                <a href="<?php echo esc_url('mailto:' . $contact['email'] . '?subject=' . rawurlencode($contact['quote_subject'])); ?>">
                    <?php echo esc_html($contact['email']); ?>
                </a>
                <a href="<?php echo esc_url(home_url('/contact/')); ?>">Contact</a>
            </div>
        </div>
    </div>

    <div class="site-header">
        <div class="container-xl sn-container site-header__inner">
            <div class="site-branding">
                <a class="site-branding__link" href="<?php echo esc_url(home_url('/')); ?>" aria-label="SONNE home">
                    <img
                        src="<?php echo esc_url($contact['logo_url']); ?>"
                        alt="<?php echo esc_attr($contact['logo_alt']); ?>"
                        class="site-branding__logo"
                        width="381"
                        height="102"
                        data-base-height="40px"
                        data-scroll-height="34px"
                    >
                </a>
            </div>

            <nav class="site-nav site-nav--desktop" aria-label="Primary navigation">
                <ul class="site-nav__list">
                    <?php foreach ($navigation as $item) : ?>
                        <?php $has_children = !empty($item['children']); ?>
                        <li class="site-nav__item<?php echo $has_children ? ' has-children' : ''; ?>">
                            <a class="site-nav__link" href="<?php echo esc_url($item['url']); ?>">
                                <?php echo esc_html($item['label']); ?>
                                <?php if ($has_children) : ?>
                                    <span class="site-nav__caret" aria-hidden="true"></span>
                                <?php endif; ?>
                            </a>

                            <?php if ($has_children && !empty($item['kind']) && 'mega' === $item['kind']) : ?>
                                <div class="site-nav__dropdown site-nav__dropdown--mega">
                                    <div class="site-nav__mega-inner">
                                        <div class="site-nav__mega-grid">
                                            <?php foreach ($item['children'] as $group) : ?>
                                                <div class="site-nav__mega-column">
                                                    <?php if (!empty($group['title'])) : ?>
                                                        <p class="site-nav__mega-title">
                                                            <a href="<?php echo esc_url($group['url']); ?>"><?php echo esc_html($group['title']); ?></a>
                                                        </p>
                                                    <?php endif; ?>
                                                    <ul class="site-nav__dropdown-list">
                                                        <?php foreach ($group['links'] as $link) : ?>
                                                            <li>
                                                                <a
                                                                    href="<?php echo esc_url($link['url']); ?>"
                                                                    class="mega-item hover-trigger"
                                                                    data-img="<?php echo esc_url(!empty($link['preview_image']) ? $link['preview_image'] : $mega_menu_defaults['default_preview_image']); ?>"
                                                                    data-alt="<?php echo esc_attr($link['label']); ?>"
                                                                >
                                                                    <?php echo esc_html($link['label']); ?>
                                                                </a>
                                                            </li>
                                                        <?php endforeach; ?>
                                                    </ul>
                                                </div>
                                            <?php endforeach; ?>
                                        </div>
                                        <div class="site-nav__mega-preview">
                                            <img
                                                src="<?php echo esc_url(!empty($item['default_preview_image']) ? $item['default_preview_image'] : $mega_menu_defaults['default_preview_image']); ?>"
                                                id="productPreviewImg"
                                                alt="<?php echo esc_attr(!empty($item['default_preview_alt']) ? $item['default_preview_alt'] : $mega_menu_defaults['default_preview_alt']); ?>"
                                                width="1024"
                                                height="1024"
                                            >
                                        </div>
                                    </div>
                                    <div class="site-nav__mega-footer">
                                        <p class="site-nav__mega-footnote">
                                            <?php echo esc_html(!empty($item['footer_copy']) ? $item['footer_copy'] : $mega_menu_defaults['footer_copy']); ?>
                                        </p>
                                        <a href="<?php echo esc_url(home_url('/products/')); ?>" class="btn-mega-action">Explore all products &rarr;</a>
                                    </div>
                                </div>
                            <?php elseif ($has_children) : ?>
                                <div class="site-nav__dropdown">
                                    <ul class="site-nav__dropdown-list">
                                        <?php foreach ($item['children'] as $child) : ?>
                                            <li>
                                                <a href="<?php echo esc_url($child['url']); ?>">
                                                    <?php echo esc_html($child['label']); ?>
                                                </a>
                                                <?php if (!empty($child['children'])) : ?>
                                                    <ul class="site-nav__dropdown-list site-nav__dropdown-list--sub">
                                                        <?php foreach ($child['children'] as $subchild) : ?>
                                                            <li>
                                                                <a href="<?php echo esc_url($subchild['url']); ?>">
                                                                    <?php echo esc_html($subchild['label']); ?>
                                                                </a>
                                                            </li>
                                                        <?php endforeach; ?>
                                                    </ul>
                                                <?php endif; ?>
                                            </li>
                                        <?php endforeach; ?>
                                    </ul>
                                </div>
                            <?php endif; ?>
                        </li>
                    <?php endforeach; ?>
                </ul>
            </nav>

            <div class="site-header__actions">
                <a class="sn-btn sn-btn--primary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">
                    Request a Quote
                </a>
                <button class="site-menu-toggle" type="button" aria-expanded="false" aria-controls="site-mobile-nav">
                    <span></span>
                    <span></span>
                    <span></span>
                    <span class="screen-reader-text">Toggle navigation</span>
                </button>
            </div>
        </div>
    </div>

    <div class="site-mobile-nav" id="site-mobile-nav" hidden>
        <div class="site-mobile-nav__panel">
            <div class="site-mobile-nav__header">
                <div>
                    <p class="site-mobile-nav__brand"><?php echo esc_html($contact['brand_name']); ?></p>
                    <p class="site-mobile-nav__subline">Custom RF, microwave and enclosure engineering.</p>
                </div>
                <button class="site-mobile-nav__close" type="button" aria-label="Close navigation">Close</button>
            </div>

            <div class="site-mobile-nav__body">
                <ul class="site-mobile-nav__list">
                    <?php foreach ($navigation as $item) : ?>
                        <?php $has_children = !empty($item['children']); ?>
                        <li class="site-mobile-nav__item">
                            <div class="site-mobile-nav__row">
                                <a class="site-mobile-nav__link" href="<?php echo esc_url($item['url']); ?>">
                                    <?php echo esc_html($item['label']); ?>
                                </a>
                                <?php if ($has_children) : ?>
                                    <button class="site-mobile-nav__toggle" type="button" aria-expanded="false">More</button>
                                <?php endif; ?>
                            </div>

                            <?php if ($has_children) : ?>
                                <div class="site-mobile-nav__submenu" hidden>
                                    <?php if (!empty($item['kind']) && 'mega' === $item['kind']) : ?>
                                        <?php foreach ($item['children'] as $group) : ?>
                                            <div class="site-mobile-nav__submenu-group">
                                                <?php if (!empty($group['title'])) : ?>
                                                    <p class="site-mobile-nav__submenu-title">
                                                        <a href="<?php echo esc_url($group['url']); ?>"><?php echo esc_html($group['title']); ?></a>
                                                    </p>
                                                <?php endif; ?>
                                                <ul>
                                                    <?php foreach ($group['links'] as $link) : ?>
                                                        <li>
                                                            <a href="<?php echo esc_url($link['url']); ?>">
                                                                <?php echo esc_html($link['label']); ?>
                                                            </a>
                                                        </li>
                                                    <?php endforeach; ?>
                                                </ul>
                                            </div>
                                        <?php endforeach; ?>
                                    <?php else : ?>
                                        <ul>
                                            <?php foreach ($item['children'] as $child) : ?>
                                                <li>
                                                    <a href="<?php echo esc_url($child['url']); ?>">
                                                        <?php echo esc_html($child['label']); ?>
                                                    </a>
                                                    <?php if (!empty($child['children'])) : ?>
                                                        <ul class="site-mobile-nav__submenu-sublist">
                                                            <?php foreach ($child['children'] as $subchild) : ?>
                                                                <li>
                                                                    <a href="<?php echo esc_url($subchild['url']); ?>">
                                                                        <?php echo esc_html($subchild['label']); ?>
                                                                    </a>
                                                                </li>
                                                            <?php endforeach; ?>
                                                        </ul>
                                                    <?php endif; ?>
                                                </li>
                                            <?php endforeach; ?>
                                        </ul>
                                    <?php endif; ?>
                                </div>
                            <?php endif; ?>
                        </li>
                    <?php endforeach; ?>
                </ul>

                <div class="site-mobile-nav__contact">
                    <a class="sn-btn sn-btn--primary" href="<?php echo esc_url(home_url('/request-a-quote/')); ?>">Request a Quote</a>
                    <a href="<?php echo esc_url('mailto:' . $contact['email']); ?>">
                        <?php echo esc_html($contact['email']); ?>
                    </a>
                    <a href="tel:<?php echo esc_attr($contact['phone_href']); ?>">
                        <?php echo esc_html($contact['phone']); ?>
                    </a>
                </div>
            </div>
        </div>
    </div>
</header>
