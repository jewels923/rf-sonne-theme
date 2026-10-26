<?php
/**
 * Author archives are not used on SONNE. Redirect to the Insights hub.
 */
wp_safe_redirect(home_url('/resources/insights/'), 301);
exit;
