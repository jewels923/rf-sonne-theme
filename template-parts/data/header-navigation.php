<?php
/**
 * SONNE primary navigation using the approved 01 information architecture.
 */

$mega_menu_defaults = array(
    'default_preview_image' => 'https://rf-sonne.com/wp-content/uploads/2026/10/card-microwave.webp',
    'default_preview_alt'   => 'Microwave and RF components',
    'footer_copy'           => 'Five core product lines for RF, microwave and precision enclosure projects.',
);

return array(
    'mega_menu_defaults' => $mega_menu_defaults,
    'navigation' => array(
        array(
            'label' => 'Products',
            'url'   => home_url('/products/'),
            'kind'  => 'mega',
            'default_preview_image' => $mega_menu_defaults['default_preview_image'],
            'default_preview_alt'   => $mega_menu_defaults['default_preview_alt'],
            'footer_copy'           => $mega_menu_defaults['footer_copy'],
            'children' => array(
                array(
                    'title' => 'RF & Microwave Filters',
                    'url'   => home_url('/products/rf-microwave-filters/'),
                    'links' => array(),
                ),
                array(
                    'title' => 'Waveguide Components',
                    'url'   => home_url('/products/waveguide-components/'),
                    'links' => array(),
                ),
                array(
                    'title' => 'RF Combiners & Duplexers',
                    'url'   => home_url('/products/rf-combiners/'),
                    'links' => array(),
                ),
                array(
                    'title' => 'Base Station RF',
                    'url'   => home_url('/products/base-station-rf/'),
                    'links' => array(),
                ),
                array(
                    'title' => 'Precision Enclosures',
                    'url'   => home_url('/products/precision-enclosures/'),
                    'links' => array(),
                ),
            ),
        ),
        array(
            'label' => 'Solutions',
            'url'   => home_url('/solutions/'),
        ),
        array(
            'label' => 'Engineering',
            'url'   => home_url('/engineering/'),
        ),
        array(
            'label' => 'Resources',
            'url'   => home_url('/resources/'),
        ),
        array(
            'label' => 'About',
            'url'   => home_url('/about/'),
        ),
        array(
            'label' => 'Contact',
            'url'   => home_url('/contact/'),
        ),
    ),
);
