<?php
get_header();

$GLOBALS['julong_header_emitted'] = true;
get_template_part('template-parts/header');
?>
<main id="main-content">
    <?php the_content(); ?>
</main>
<?php
get_template_part('template-parts/footer');

get_footer();
