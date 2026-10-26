<?php
get_header();

// Flag: page.php has already output the branded header at the top of the page.
// functions.php's generate_before_content hook checks this and skips its own output.
$GLOBALS['julong_header_emitted'] = true;
get_template_part('template-parts/header');
?>
<main id="main-content">
    <?php the_content(); ?>
</main>
<?php
get_template_part('template-parts/footer');

get_footer();
