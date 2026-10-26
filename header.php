<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <?php
    // Rank Math omits the canonical site-wide, so buffer wp_head and append one
    // only when no canonical tag was printed.
    ob_start();
    wp_head();
    $sonne_head = ob_get_clean();
    echo $sonne_head;
    if (!preg_match('/<link[^>]+rel=["\']canonical["\']/i', $sonne_head)) {
        $sonne_canonical = function_exists('sonne_current_canonical_url') ? sonne_current_canonical_url() : '';
        if ($sonne_canonical) {
            echo '<link rel="canonical" href="' . esc_url($sonne_canonical) . '" />' . "\n";
        }
    }
    ?>
</head>
<body <?php body_class(); ?>>
    <?php wp_body_open(); ?>
