<?php
/**
 * Floating WhatsApp chat dialog, rendered site-wide in the footer.
 *
 * Copy stays in English so TranslatePress can map it per language.
 */

if (!defined('ABSPATH')) {
    exit;
}

if (!function_exists('sonne_whatsapp_chat_config')) {
    function sonne_whatsapp_chat_config() {
        static $config = null;
        if ($config === null) {
            $contact = require get_stylesheet_directory() . '/template-parts/data/site-contact.php';
            $config = array(
                'number'  => $contact['whatsapp_href'],
                'display' => $contact['whatsapp'],
            );
        }
        return $config;
    }
}

if (!function_exists('sonne_render_whatsapp_chat')) {
    function sonne_render_whatsapp_chat() {
        if (is_admin()) {
            return;
        }

        $config = sonne_whatsapp_chat_config();
        $wa_url = 'https://wa.me/' . $config['number'];
        ?>
        <div class="wa-chat" data-wa-chat data-wa-number="<?php echo esc_attr($config['number']); ?>">
            <a class="wa-chat__toggle" href="<?php echo esc_url($wa_url); ?>" target="_blank" rel="noopener" data-wa-toggle aria-expanded="false" aria-controls="wa-chat-panel" aria-label="Chat on WhatsApp">
                <svg class="wa-chat__glyph" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/>
                </svg>
            </a>
            <div class="wa-chat__panel" id="wa-chat-panel" role="dialog" aria-modal="false" aria-labelledby="wa-chat-title" aria-describedby="wa-chat-desc" tabindex="-1" data-wa-panel hidden>
                <div class="wa-chat__header">
                    <span class="wa-chat__avatar" aria-hidden="true">
                        <svg viewBox="0 0 24 24" fill="currentColor" focusable="false">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/>
                        </svg>
                    </span>
                    <div class="wa-chat__identity">
                        <p class="wa-chat__title" id="wa-chat-title">SONNE</p>
                        <p class="wa-chat__subtitle" id="wa-chat-desc">WhatsApp · <span dir="ltr"><?php echo esc_html($config['display']); ?></span></p>
                    </div>
                    <button class="wa-chat__close" type="button" data-wa-close aria-label="Close chat">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true" focusable="false">
                            <path d="M6 6l12 12M18 6L6 18"/>
                        </svg>
                    </button>
                </div>
                <div class="wa-chat__body">
                    <p class="wa-chat__bubble"><?php echo esc_html('Hi! How can we help with your RF or microwave project?'); ?></p>
                    <p class="wa-chat__bubble"><?php echo esc_html("Tell us what you need and we'll continue the conversation on WhatsApp."); ?></p>
                </div>
                <form class="wa-chat__composer" data-wa-form action="<?php echo esc_url($wa_url); ?>" method="get" target="_blank" accept-charset="UTF-8">
                    <label class="wa-chat__label" for="wa-chat-input"><?php echo esc_html('Message'); ?></label>
                    <textarea class="wa-chat__input" id="wa-chat-input" name="text" rows="1" maxlength="1000" data-wa-input placeholder="<?php echo esc_attr('Type your message…'); ?>"></textarea>
                    <button class="wa-chat__send" type="submit" aria-label="Send on WhatsApp">
                        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
                            <path d="M2.01 21 23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </form>
            </div>
        </div>
        <?php
    }
}
add_action('wp_footer', 'sonne_render_whatsapp_chat', 30);
