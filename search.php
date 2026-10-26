<?php
get_header();

get_template_part('template-parts/header');

if (have_posts()) {
    while (have_posts()) {
        the_post();
        // get_template_part('template-parts/content', get_post_type());
    }
}

get_template_part('template-parts/footer');

get_footer();
