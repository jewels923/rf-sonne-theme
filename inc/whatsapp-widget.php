<?php
/**
 * KJbath Global WhatsApp / WeChat Chat Widget
 * Adapted from Sanyang Medical demo widget. Dark theme (#16191f + gold #d7ae43).
 */
function kjbath_inject_global_widget() {
    $contact = require __DIR__ . '/template-parts/data/site-contact.php';
    $brand_name = $contact['brand_name'];
    $phone_display = $contact['phone_display'];
    $whatsapp_number = preg_replace('/\D+/', '', $contact['phone_link']);
    $wechat_id = '+86 13450284642';
    ?>
    <div id="kjbath-wa-widget">
        <div id="wa-smart-toast" class="wa-engagement-bubble">
            <div class="bubble-content" id="bubble-text-container">
                <strong id="hook-title">Need a fast quotation?</strong>
                <span class="sub-text" id="hook-sub">Chat with our export team on WhatsApp.</span>
            </div>
            <button class="bubble-close" onclick="closeWaToast(event)">&times;</button>
            <div class="bubble-arrow"></div>
        </div>

        <div id="wa-chat-box" class="wa-box" role="dialog" aria-labelledby="wa-chat-title" aria-hidden="true">
            <div class="wa-box-header">
                <div class="wa-header-info">
                    <div class="wa-name" id="wa-chat-title"><?php echo esc_html($brand_name); ?></div>
                    <div class="wa-status">Online • Sports Eyewear Factory Support</div>
                </div>
                <button id="wa-minimize-btn" type="button" title="Close" aria-label="Close chat channels">&times;</button>
            </div>

            <div class="wa-channel-tabs" role="tablist" aria-label="Chat channels">
                <button class="tab-btn active" type="button" data-target="whatsapp" role="tab" aria-selected="true" aria-controls="view-whatsapp" id="wa-tab-whatsapp">
                    <svg viewBox="0 0 24 24" fill="#25D366" width="16" height="16"><path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0 0 12.04 2zM12.05 20.21c-1.5 0-2.97-.39-4.27-1.14l-.3-.18-3.17.83.84-3.07-.18-.3a8.203 8.203 0 0 1-1.14-4.28c0-4.57 3.73-8.27 8.3-8.27 2.21 0 4.29.86 5.85 2.42a8.23 8.23 0 0 1 2.43 5.83c-.01 4.56-3.73 8.26-8.3 8.26zM16.6 14.3c-.25-.13-1.47-.72-1.69-.81-.23-.08-.39-.13-.56.13-.17.25-.66.81-.81.97-.15.17-.29.19-.54.06-.25-.13-1.05-.39-1.99-1.23-.74-.66-1.23-1.47-1.38-1.72-.14-.25-.02-.38.11-.51.11-.11.25-.29.37-.43s.17-.25.25-.41c.08-.17.04-.31-.02-.43s-.56-1.34-.76-1.84c-.2-.48-.41-.42-.56-.43h-.48c-.17 0-.43.06-.66.31-.22.25-.86.85-.86 2.07 0 1.22.89 2.4 1.01 2.56.12.17 1.75 2.67 4.23 3.74.59.26 1.05.41 1.41.52.59.19 1.13.16 1.56.1.48-.07 1.47-.6 1.67-1.18.21-.58.21-1.07.14-1.18s-.27-.16-.51-.29z"/></svg>
                    WhatsApp
                </button>
                <button class="tab-btn" type="button" data-target="wechat" role="tab" aria-selected="false" aria-controls="view-wechat" id="wa-tab-wechat">
                    <svg viewBox="0 0 24 24" fill="#07C160" width="18" height="18"><path d="M8.5,13.8c-4.1,0-7.5-3.1-7.5-7s3.4-7,7.5-7s7.5,3.1,7.5,7S12.6,13.8,8.5,13.8z M8.9,4.5c-0.6,0-1,0.4-1,1s0.4,1,1,1 s1-0.4,1-1S9.4,4.5,8.9,4.5z M5.4,4.5c-0.6,0-1,0.4-1,1s0.4,1,1,1s1-0.4,1-1S5.9,4.5,5.4,4.5z"/><path d="M17,23l-1.9-1c-0.7,0.2-1.4,0.3-2.1,0.3c-3.6,0-6.5-2.7-6.5-6c0-0.1,0-0.3,0-0.4c0.6,0.1,1.3,0.1,2,0.1c4.7,0,8.5-3.6,8.5-8 c0-0.5-0.1-1-0.2-1.5c2.9,0.9,4.9,3.4,4.9,6.2C21.7,16.3,19.7,19,17,23z M15.5,16c-0.5,0-0.9,0.4-0.9,0.9s0.4,0.9,0.9,0.9 s0.9-0.4,0.9-0.9S16,16,15.5,16z M18.5,16c-0.5,0-0.9,0.4-0.9,0.9s0.4,0.9,0.9,0.9s0.9-0.4,0.9-0.9S19,16,18.5,16z"/></svg>
                    WeChat
                </button>
            </div>

            <div class="wa-box-body">
                <div id="view-whatsapp" class="tab-content active" role="tabpanel" aria-labelledby="wa-tab-whatsapp">
                    <div class="wa-msg-received">
                        Hello from <?php echo esc_html($brand_name); ?>.
                        <span class="wa-time">Just now</span>
                    </div>
                    <div class="wa-msg-received">
                        Send us your project scope, drawings, or target model. We reply on WhatsApp at <?php echo esc_html($phone_display); ?>.
                        <span class="wa-time">Just now</span>
                    </div>
                </div>

                <div id="view-wechat" class="tab-content" role="tabpanel" aria-labelledby="wa-tab-wechat" aria-hidden="true" style="display: none; text-align: center; padding-top: 10px;">
                    <div class="wechat-id-card">
                        <span class="scan-tip">WeChat ID</span>
                        <div class="wechat-id-number"><?php echo esc_html($wechat_id); ?></div>
                    </div>
                    <div class="wa-msg-received wa-msg-received--center">
                        Add us on WeChat with this ID, or send us your WeChat ID on WhatsApp and we will add you first.
                    </div>
                </div>
            </div>

            <div class="wa-box-footer" id="wa-input-area">
                <input type="text" id="wa-user-input" placeholder="Type your inquiry..." aria-label="Type your inquiry" />
                <button id="wa-send-btn" type="button" aria-label="Send WhatsApp message">
                    <span class="icon-send-fallback" aria-hidden="true">&#10148;</span>
                </button>
            </div>
        </div>

        <button id="wa-trigger-btn" class="wa-expand-btn" type="button" aria-label="Open chat channels" aria-controls="wa-chat-box" aria-expanded="false" aria-haspopup="dialog">
            <div class="wa-icon-box">
                <svg viewBox="0 0 24 24" fill="none" class="wa-trigger-mobile-icon" aria-hidden="true">
                    <path d="M7 9.5h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    <path d="M7 13.5h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    <path d="M12 3.5c4.97 0 9 3.58 9 8s-4.03 8-9 8c-.9 0-1.77-.12-2.58-.36L4 21l1.7-4.21C4.64 15.42 3 13.56 3 11.5c0-4.42 4.03-8 9-8Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
                </svg>
                <svg viewBox="0 0 24 24" fill="#fff" class="icon-wa">
                    <path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0 0 12.04 2zM12.05 20.21c-1.5 0-2.97-.39-4.27-1.14l-.3-.18-3.17.83.84-3.07-.18-.3a8.203 8.203 0 0 1-1.14-4.28c0-4.57 3.73-8.27 8.3-8.27 2.21 0 4.29.86 5.85 2.42a8.23 8.23 0 0 1 2.43 5.83c-.01 4.56-3.73 8.26-8.3 8.26z"/>
                </svg>
                <span class="icon-divider">/</span>
                <svg viewBox="0 0 24 24" fill="#fff" class="icon-wechat">
                    <path d="M8.5,13.8c-4.1,0-7.5-3.1-7.5-7s3.4-7,7.5-7s7.5,3.1,7.5,7S12.6,13.8,8.5,13.8z M8.9,4.5c-0.6,0-1,0.4-1,1s0.4,1,1,1 s1-0.4,1-1S9.4,4.5,8.9,4.5z M5.4,4.5c-0.6,0-1,0.4-1,1s0.4,1,1,1s1-0.4,1-1S5.9,4.5,5.4,4.5z"/>
                    <path d="M17,23l-1.9-1c-0.7,0.2-1.4,0.3-2.1,0.3c-3.6,0-6.5-2.7-6.5-6c0-0.1,0-0.3,0-0.4c0.6,0.1,1.3,0.1,2,0.1c4.7,0,8.5-3.6,8.5-8 c0-0.5-0.1-1-0.2-1.5c2.9,0.9,4.9,3.4,4.9,6.2C21.7,16.3,19.7,19,17,23z M15.5,16c-0.5,0-0.9,0.4-0.9,0.9s0.4,0.9,0.9,0.9 s0.9-0.4,0.9-0.9S16,16,15.5,16z M18.5,16c-0.5,0-0.9,0.4-0.9,0.9s0.4,0.9,0.9,0.9s0.9-0.4,0.9-0.9S19,16,18.5,16z"/>
                </svg>
            </div>
            <div class="wa-expand-text">
                <span class="label">Need Support?</span>
                <span class="action">Chat Now</span>
            </div>
        </button>
    </div>
    <style>
        :root {
            --wa-mobile-trigger-bottom: 24px;
            --wa-mobile-trigger-right: 16px;
            --wa-mobile-trigger-size: 60px;
            --wa-mobile-drawer-gap: 12px;
            --wa-mobile-safe-stack: 0px;
        }
        #kjbath-wa-widget { position: fixed; right: 0; top: 78%; margin-top: -27px; z-index: 1085; font-family: var(--font-body, 'Helvetica Neue', Helvetica, Arial, sans-serif); display: flex; flex-direction: column; align-items: flex-end; transition: opacity 0.2s ease, transform 0.2s ease; }
        body.site-nav-open #kjbath-wa-widget,
        body.site-footer-modal-open #kjbath-wa-widget { opacity: 0; pointer-events: none; transform: translateY(8px); }
        .wa-engagement-bubble { position: absolute; bottom: 75px; right: 20px; width: 260px; background: #fff; padding: 15px; border-radius: 8px; box-shadow: -5px 5px 25px rgba(0,0,0,0.15); border-right: 4px solid #d7ae43; opacity: 0; transform: translateX(20px); visibility: hidden; transition: opacity 0.4s, transform 0.4s; z-index: 100000; cursor: pointer; }
        .wa-engagement-bubble.active { opacity: 1; transform: translateX(0); visibility: visible; }
        .wa-engagement-bubble .bubble-content { text-align: right; padding-right: 5px; transition: opacity 0.3s; }
        .wa-engagement-bubble .bubble-content.fading { opacity: 0; }
        .wa-engagement-bubble strong { display: block; color: #16191f; font-size: 13px; margin-bottom: 4px; font-weight: 700; line-height: 1.4; }
        .wa-engagement-bubble .sub-text { font-size: 11px; color: #5b5b64; display: block; line-height: 1.35; }
        .wa-engagement-bubble .bubble-arrow { position: absolute; bottom: -6px; right: 20px; width: 12px; height: 12px; background: #fff; transform: rotate(45deg); }
        .wa-engagement-bubble .bubble-close { position: absolute; top: 5px; left: 5px; background: none; border: none; color: #b6bcc8; font-size: 18px; cursor: pointer; padding: 0; min-width: 44px; min-height: 44px; display: inline-flex; align-items: center; justify-content: center; }
        .wa-engagement-bubble .bubble-close:hover { color: #16191f; }

        .wa-box { position: absolute; bottom: 75px; right: 20px; width: 340px; max-height: calc(100vh - 130px); display: flex; flex-direction: column; background: #fff; border-radius: 12px; box-shadow: -10px 20px 50px rgba(0,0,0,0.2); overflow: hidden; opacity: 0; visibility: hidden; transform: translateX(20px) scale(0.95); transform-origin: bottom right; transition: all 0.25s cubic-bezier(0.19, 1, 0.22, 1); border: 1px solid #e8edf5; }
        .wa-box.is-open { opacity: 1; visibility: visible; transform: translateX(0) scale(1); }
        .wa-box-header { background: linear-gradient(135deg, #16191f 0%, #23272f 100%); padding: 15px; display: flex; align-items: center; color: #fff; justify-content: space-between; border-bottom: 1px solid rgba(215,174,67,0.35); }
        .wa-name { font-weight: 700; font-size: 15px; letter-spacing: 0.2px; }
        .wa-status { font-size: 11px; opacity: 0.82; margin-top: 2px; }
        #wa-minimize-btn { background: none; border: none; color: #fff; font-size: 24px; cursor: pointer; opacity: 0.8; min-width: 44px; min-height: 44px; display: inline-flex; align-items: center; justify-content: center; }
        #wa-minimize-btn:hover { opacity: 1; }

        .wa-channel-tabs { display: flex; background: #f8fafc; border-bottom: 1px solid #e8edf5; }
        .tab-btn { flex: 1; border: none; background: transparent; padding: 12px; font-size: 12px; font-weight: 600; color: #5b5b64; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; transition: all 0.2s; position: relative; }
        .tab-btn:hover { background: #f0f1f3; }
        .tab-btn.active { background: #fff; color: #16191f; }
        .tab-btn.active::after { content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 2px; background: #d7ae43; }

        .wa-box-body { background: #f7f7f5; padding: 20px 15px; height: 320px; flex: 1 1 auto; min-height: 0; overflow-y: auto; }
        .wa-msg-received { background: #fff; padding: 10px 14px; border-radius: 0 10px 10px 10px; font-size: 13px; color: #2f3640; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 10px; max-width: 90%; line-height: 1.55; border: 1px solid #e8edf5; }
        .wa-msg-received--center { margin: 15px auto; text-align: center; max-width: 100%; }
        .wa-time { display: block; font-size: 10px; color: #8d96a5; margin-top: 4px; text-align: right; }
        .scan-tip { font-size: 11px; color: #687385; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; display: block; }
        .wechat-id-card { background: #16191f; padding: 18px 20px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 15px rgba(0,0,0,0.12); margin-bottom: 5px; border: 1px solid rgba(215,174,67,0.45); }
        .wechat-id-card .scan-tip { color: #d7ae43; }
        .wechat-id-number { font-size: 22px; font-weight: 700; color: #fff; letter-spacing: 0.5px; user-select: all; }

        .wa-box-footer { padding: 12px; background: #fff; display: flex; align-items: center; gap: 10px; border-top: 1px solid #e8edf5; transition: all 0.3s; }
        #wa-user-input { flex: 1; border: 1px solid #e3e3e0; padding: 10px 12px; border-radius: 8px; outline: none; background: #fcfcfb; font-size: 13px; }
        #wa-user-input:focus { background: #fff; border-color: #d7ae43; }
        #wa-send-btn { background: #25D366; border: none; width: 40px; height: 40px; min-width: 40px; border-radius: 50%; color: #ffffff !important; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: transform 0.2s; position: relative; z-index: 2; }
        #wa-send-btn:hover { transform: scale(1.1); background: #1ebe57; color: #ffffff !important; }
        .icon-send-fallback { display: inline-flex; align-items: center; justify-content: center; font-size: 18px; line-height: 1; color: #ffffff !important; font-weight: 700; transform: translateX(1px); }

        .wa-expand-btn { display: flex; align-items: center; flex-direction: row-reverse; background: linear-gradient(135deg, #16191f 0%, #23272f 100%); color: #fff; height: 56px; width: 76px; border-top-left-radius: 28px; border-bottom-left-radius: 28px; box-shadow: 0 8px 18px rgba(22,25,31,0.35); transition: width 0.3s cubic-bezier(0.25, 1, 0.5, 1), background-color 0.3s, opacity 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease; overflow: hidden; cursor: pointer; border: 1px solid rgba(215,174,67,0.35); border-right: none; padding: 0; appearance: none; -webkit-appearance: none; }
        .wa-expand-btn:focus-visible { outline: 2px solid rgba(215,174,67,0.8); outline-offset: 3px; }
        .wa-icon-box { width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; gap: 3px; }
        .wa-trigger-mobile-icon { display: none; width: 24px; height: 24px; color: currentColor; }
        .icon-wa { width: 20px; height: 20px; }
        .icon-wechat { width: 22px; height: 22px; margin-top: 2px; }
        .icon-divider { font-size: 14px; opacity: 0.6; font-weight: 300; margin: 0 1px; }
        .wa-expand-text { display: flex; flex-direction: column; justify-content: center; padding-left: 15px; padding-right: 5px; text-align: right; opacity: 0; transition: opacity 0.2s delay 0.1s; white-space: nowrap; }
        @media (hover: hover) and (pointer: fine) {
            .wa-expand-btn:hover { width: 220px; background: linear-gradient(135deg, #23272f 0%, #2e333c 100%); }
            .wa-expand-btn:hover .wa-expand-text { opacity: 1; }
        }
        .wa-expand-text .label { font-size: 10px; text-transform: uppercase; font-weight: 700; opacity: 0.8; letter-spacing: 0.5px; line-height: 1.2; }
        .wa-expand-text .action { font-size: 13px; font-weight: 700; line-height: 1.2; }

        @media (max-width: 768px) {
            #kjbath-wa-widget { right: var(--wa-mobile-trigger-right); top: auto; bottom: var(--wa-mobile-trigger-bottom); margin-top: 0; }
            .wa-expand-btn { border-radius: 50%; width: var(--wa-mobile-trigger-size); height: var(--wa-mobile-trigger-size); min-width: var(--wa-mobile-trigger-size); flex-direction: row; border-top-left-radius: 50%; border-bottom-left-radius: 50%; background: rgba(22, 25, 31, 0.88); border: 1px solid rgba(215,174,67,0.4); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); box-shadow: 0 14px 32px rgba(20,20,20,0.22); opacity: 0.9; }
            .wa-expand-btn:hover { width: 52px; background: rgba(22, 25, 31, 0.96); }
            .wa-expand-btn:active,
            .wa-expand-btn.is-active { opacity: 1; transform: translateY(-1px); }
            .wa-expand-text { display: none; }
            .wa-box { position: fixed; left: 12px; right: 12px; bottom: calc(var(--wa-mobile-trigger-bottom) + var(--wa-mobile-trigger-size) + var(--wa-mobile-drawer-gap) + var(--wa-mobile-safe-stack)); width: auto; max-width: none; max-height: min(82vh, 640px); border-radius: 22px; transform-origin: bottom center; transform: translateY(18px) scale(0.98); box-shadow: 0 20px 48px rgba(0,0,0,0.24); }
            .wa-box.is-open { transform: translateY(0) scale(1); }
            .wa-box-header { padding: 16px 18px; }
            .wa-channel-tabs { min-height: 48px; }
            .tab-btn { min-height: 48px; font-size: 13px; }
            #wa-user-input { font-size: 16px; }
            .wa-box-body { height: auto; max-height: calc(min(82vh, 640px) - 144px); padding: 16px 14px; }
            .wa-engagement-bubble { display: none !important; bottom: 90px; right: 0; width: 220px; }
            .wa-icon-box { width: 52px; height: 52px; gap: 0; }
            .wa-trigger-mobile-icon { display: block; }
            .icon-wa, .icon-wechat, .icon-divider { display: none; }
        }
    </style>
    <script>
    (function() {
        const widgetRoot = document.getElementById('kjbath-wa-widget');
        const triggerBtn = document.getElementById('wa-trigger-btn');
        const chatBox = document.getElementById('wa-chat-box');
        const closeBtn = document.getElementById('wa-minimize-btn');
        const sendBtn = document.getElementById('wa-send-btn');
        const userInput = document.getElementById('wa-user-input');
        const inputArea = document.getElementById('wa-input-area');
        const toast = document.getElementById('wa-smart-toast');
        const toastContent = document.getElementById('bubble-text-container');
        const hookTitle = document.getElementById('hook-title');
        const hookSub = document.getElementById('hook-sub');
        const tabs = document.querySelectorAll('.tab-btn');
        const contents = document.querySelectorAll('.tab-content');
        const mobileQuery = window.matchMedia('(max-width: 768px)');
        let mobileLayoutTicking = false;
        let lastActiveElement = null;

        const phone = "<?php echo esc_js($whatsapp_number); ?>";
        let activeChannel = 'whatsapp';

        const funHooks = [
            { t: "Need a fast quotation?", s: "Message our export team on WhatsApp." },
            { t: "Launching an eyewear line?", s: "Send your target styles and quantities." },
            { t: "Looking for OEM or wholesale pricing?", s: "We can reply with the right product path." },
            { t: "Need catalog and certificates?", s: "WhatsApp us and we will send them quickly." },
            { t: "Working on a custom eyewear design?", s: "Tell us the frame, lens, and logo options." }
        ];

        let rotationInterval;
        let isPaused = false;

        function isMobileView() {
            return mobileQuery.matches;
        }

        function setChatOpenState(isOpen) {
            chatBox.classList.toggle('is-open', isOpen);
            triggerBtn.classList.toggle('is-active', isOpen);
            triggerBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            chatBox.setAttribute('aria-hidden', isOpen ? 'false' : 'true');

            if (window.__lenis) {
                if (isOpen) {
                    window.__lenis.stop();
                } else {
                    window.__lenis.start();
                }
            }

            if (isOpen) {
                lastActiveElement = document.activeElement;
                toast.classList.remove('active');
                stopRotation();
                syncMobileDrawerOffset();
                if (activeChannel === 'whatsapp') {
                    setTimeout(() => userInput.focus(), 220);
                }
            } else if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
                lastActiveElement.focus();
            }
        }

        function getMobileFloatingObstacles() {
            return Array.from(document.querySelectorAll('body *')).filter((element) => {
                if (!element || !element.getBoundingClientRect) return false;
                if (element === document.body || element === document.documentElement) return false;
                if (widgetRoot.contains(element) || element.closest('#kjbath-wa-widget')) return false;

                const styles = window.getComputedStyle(element);
                if (!['fixed', 'sticky'].includes(styles.position)) return false;
                if (styles.display === 'none' || styles.visibility === 'hidden' || Number(styles.opacity || '1') === 0) return false;

                const rect = element.getBoundingClientRect();
                if (rect.width < 32 || rect.height < 32) return false;
                if (rect.bottom <= 0 || rect.top >= window.innerHeight) return false;

                const bottomGap = window.innerHeight - rect.bottom;
                const nearBottomEdge = bottomGap <= 32 || rect.top >= window.innerHeight - 180;
                return nearBottomEdge;
            });
        }

        function syncMobileDrawerOffset() {
            if (!widgetRoot) return;

            let safeStack = 0;
            if (isMobileView()) {
                getMobileFloatingObstacles().forEach((element) => {
                    const rect = element.getBoundingClientRect();
                    safeStack = Math.max(safeStack, (window.innerHeight - rect.top) + 12);
                });
            }

            const stackPx = Math.max(0, Math.round(safeStack));
            document.documentElement.style.setProperty('--wa-mobile-safe-stack', `${stackPx}px`);

            if (isMobileView() && stackPx > 0) {
                widgetRoot.style.bottom = `calc(24px + ${stackPx}px)`;
            } else {
                widgetRoot.style.bottom = '';
            }
        }

        function syncViewportMode() {
            syncMobileDrawerOffset();
            if (isMobileView()) {
                toast.classList.remove('active');
                stopRotation();
            }
        }

        function rotateHook() {
            if (isPaused) return;
            toastContent.classList.add('fading');
            setTimeout(() => {
                const randomHook = funHooks[Math.floor(Math.random() * funHooks.length)];
                hookTitle.innerText = randomHook.t;
                hookSub.innerText = randomHook.s;
                toastContent.classList.remove('fading');
            }, 500);
        }

        function startRotation() {
            if (rotationInterval) clearInterval(rotationInterval);
            rotationInterval = setInterval(rotateHook, 6000);
        }

        function stopRotation() {
            clearInterval(rotationInterval);
        }

        toast.addEventListener('mouseenter', () => { isPaused = true; });
        toast.addEventListener('mouseleave', () => { isPaused = false; });

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => {
                    t.classList.remove('active');
                    t.setAttribute('aria-selected', 'false');
                });
                tab.classList.add('active');
                tab.setAttribute('aria-selected', 'true');

                const target = tab.dataset.target;
                contents.forEach(c => {
                    c.style.display = 'none';
                    c.setAttribute('aria-hidden', 'true');
                });
                document.getElementById(`view-${target}`).style.display = 'block';
                document.getElementById(`view-${target}`).setAttribute('aria-hidden', 'false');
                activeChannel = target;

                if (target === 'wechat') {
                    inputArea.style.display = 'none';
                } else {
                    inputArea.style.display = 'flex';
                    setTimeout(() => userInput.focus(), 100);
                }
            });
        });

        triggerBtn.setAttribute('aria-expanded', 'false');
        triggerBtn.addEventListener('click', function() {
            setChatOpenState(!chatBox.classList.contains('is-open'));
        });

        closeBtn.addEventListener('click', () => setChatOpenState(false));
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && chatBox.classList.contains('is-open')) {
                setChatOpenState(false);
            }
        });

        function sendMessage() {
            const msg = userInput.value.trim();
            if (msg === "") return;

            const finalMsg = `*New Inquiry from JulongEyewear.com*\n------------------\n*Message:* ${msg}`;
            const url = `https://wa.me/${phone}?text=${encodeURIComponent(finalMsg)}`;
            window.open(url, '_blank');

            userInput.value = "";
            setChatOpenState(false);
        }

        sendBtn.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

        window.closeWaToast = function(e) {
            e.stopPropagation();
            toast.classList.remove('active');
            stopRotation();
            sessionStorage.setItem('waToastDismissed', 'true');
        };

        toast.addEventListener('click', (e) => {
            if (!e.target.classList.contains('bubble-close')) triggerBtn.click();
        });

        function requestMobileLayoutSync() {
            if (mobileLayoutTicking) return;
            mobileLayoutTicking = true;
            window.requestAnimationFrame(() => {
                syncViewportMode();
                mobileLayoutTicking = false;
            });
        }

        window.addEventListener('scroll', requestMobileLayoutSync, { passive: true });
        window.addEventListener('resize', requestMobileLayoutSync);
        window.addEventListener('load', requestMobileLayoutSync);
        window.setTimeout(requestMobileLayoutSync, 300);
        window.setTimeout(requestMobileLayoutSync, 1200);

        if (typeof mobileQuery.addEventListener === 'function') {
            mobileQuery.addEventListener('change', requestMobileLayoutSync);
        } else if (typeof mobileQuery.addListener === 'function') {
            mobileQuery.addListener(requestMobileLayoutSync);
        }

        setTimeout(() => {
            if (!isMobileView() && !sessionStorage.getItem('waToastDismissed') && !chatBox.classList.contains('is-open')) {
                toast.classList.add('active');
                startRotation();
            }
        }, 2500);
    })();
    </script>
    <?php
}
add_action('wp_footer', 'kjbath_inject_global_widget');
