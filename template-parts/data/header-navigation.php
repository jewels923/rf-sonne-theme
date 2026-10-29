<?php
/**
 * SONNE primary navigation using the approved 01 information architecture.
 */

$mega_menu_defaults = array(
    'default_preview_image' => 'https://rf-sonne.com/wp-content/uploads/2026/10/card-microwave.webp',
    'default_preview_alt'   => 'Microwave and RF components',
    'footer_copy'           => 'Five passive component lines and five system and active RF lines for RF, microwave and precision enclosure projects.',
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
                    'title' => 'Components',
                    'url'   => home_url('/products/#core-lines'),
                    'links' => array(
                        array(
                            'label' => 'RF & Microwave Filters',
                            'url'   => home_url('/products/rf-microwave-filters/'),
                        ),
                        array(
                            'label' => 'Waveguide Components',
                            'url'   => home_url('/products/waveguide-components/'),
                        ),
                        array(
                            'label' => 'RF Combiners & Duplexers',
                            'url'   => home_url('/products/rf-combiners/'),
                        ),
                        array(
                            'label' => 'Base Station RF',
                            'url'   => home_url('/products/base-station-rf/'),
                        ),
                        array(
                            'label' => 'Precision Enclosures',
                            'url'   => home_url('/products/precision-enclosures/'),
                        ),
                    ),
                ),
                array(
                    'title' => 'Systems & Active RF',
                    'url'   => home_url('/products/#systems'),
                    'links' => array(
                        array(
                            'label' => 'Antenna Test Systems',
                            'url'   => home_url('/products/antenna-test-systems/'),
                        ),
                        array(
                            'label' => 'Switch Matrices',
                            'url'   => home_url('/products/switch-matrices/'),
                        ),
                        array(
                            'label' => 'T/R Modules',
                            'url'   => home_url('/products/tr-modules/'),
                        ),
                        array(
                            'label' => 'Passive Microwave Components',
                            'url'   => home_url('/products/passive-microwave-components/'),
                        ),
                        array(
                            'label' => 'RF Front-Ends',
                            'url'   => home_url('/products/rf-front-ends/'),
                        ),
                    ),
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
