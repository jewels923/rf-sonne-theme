/**
 * WXKN Preview Chat Widget
 * Floating AI chat widget for WordPress preview pages.
 * Self-contained IIFE with embedded CSS, drag, localStorage persistence, and AJAX messaging.
 */
(function () {
    'use strict';

    /* ========================================================================
     * 1. CONFIG
     * ======================================================================== */

    var CONFIG = {
        ajaxUrl: window.wxknPreviewChat?.ajaxUrl || '/wp-admin/admin-ajax.php',
        streamUrl: window.wxknPreviewChat?.streamUrl || '/wp-admin/admin-ajax.php',
        nonce: window.wxknPreviewChat?.nonce || '',
        backupNonce: window.wxknPreviewChat?.backupNonce || '',
        postId: window.wxknPreviewChat?.postId || 0,
        storageKeyPos: 'wxkn_chat_position',
        storageKeyHistory: function (id) { return 'wxkn_chat_history_' + id; },
    };

    var TOOL_LABELS = {
        'read_page':    '读取页面内容',
        'update_draft': '保存草稿',
        'read_file':    '读取文件',
        'write_file':   '写入文件',
        'list_files':   '列出文件',
        'list_pages':   '列出页面',
        'publish_page': '发布页面',
    };

    // Init guard -- bail out if no post ID or nonce
    if (!CONFIG.postId || !CONFIG.nonce) {
        return;
    }

    /* ========================================================================
     * 2. STATE
     * ======================================================================== */

    var state = {
        position: { x: 20, y: 20 },
        history: [],
        expanded: false,
        sending: false,
        dragging: false,
        dragOffsetX: 0,
        dragOffsetY: 0,
        mode: 'chat',
        targets: [],
        selectedTarget: null,
        backups: [],
        selectedVersion: null,
        previewContent: '',
        stepListEl: null,
        inlineEdit: {
            originalText: '',
            newText: '',
            range: null,
            rangeRect: null,
            action: '',
            processing: false,
        },
    };

    var fab = null;
    var widget = null;
    var bodyEl = null;
    var inputEl = null;
    var sendBtn = null;
    var headerEl = null;
    var historyPanel = null;
    var fabBtn = null;
    var fabMenu = null;

    /* ========================================================================
     * 3. CSS INJECTION
     * ======================================================================== */

    function injectStyles() {
        var css = [
            '.wxkn-chat-fab{',
            'position:fixed;bottom:24px;right:24px;',
            'width:56px;height:56px;border-radius:50%;',
            'background:#2563eb;color:#fff;',
            'border:none;cursor:pointer;z-index:999999;',
            'box-shadow:0 4px 12px rgba(0,0,0,.25);',
            'display:flex;align-items:center;justify-content:center;',
            'font-size:18px;font-weight:700;',
            'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;',
            'transition:transform .2s ease,box-shadow .2s ease;',
            '}',
            '.wxkn-chat-fab:hover{transform:scale(1.08);box-shadow:0 6px 20px rgba(0,0,0,.35);}',
            '',
            '.wxkn-chat-widget{',
            'position:fixed;z-index:999998;',
            'width:380px;height:520px;',
            'background:#fff;border-radius:12px;',
            'box-shadow:0 8px 32px rgba(0,0,0,.2);',
            'display:flex;flex-direction:column;overflow:hidden;',
            'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;',
            '}',
            '',
            '.wxkn-chat-header{',
            'display:flex;align-items:center;justify-content:space-between;',
            'padding:12px 16px;background:#1e293b;color:#fff;',
            'cursor:move;user-select:none;flex-shrink:0;',
            '}',
            '.wxkn-chat-header-title{font-size:14px;font-weight:600;}',
            '.wxkn-chat-header-actions{display:flex;gap:8px;}',
            '.wxkn-chat-header-btn{',
            'background:none;border:none;color:#94a3b8;cursor:pointer;',
            'padding:4px;font-size:14px;line-height:1;',
            '}',
            '.wxkn-chat-header-btn:hover{color:#fff;}',
            '',
            '.wxkn-chat-body{',
            'flex:1;overflow-y:auto;padding:16px;',
            'display:flex;flex-direction:column;gap:10px;',
            'background:#f8fafc;',
            '}',
            '',
            '.wxkn-chat-msg{',
            'max-width:85%;padding:10px 14px;border-radius:12px;',
            'font-size:13px;line-height:1.5;word-break:break-word;',
            '}',
            '.wxkn-chat-msg-user{',
            'align-self:flex-end;background:#2563eb;color:#fff;',
            'border-bottom-right-radius:4px;',
            '}',
            '.wxkn-chat-msg-ai,.wxkn-chat-msg-assistant{',
            'align-self:flex-end;background:#f1f5f9;color:#1e293b;',
            'border-bottom-left-radius:4px;',
            '}',
            '.wxkn-chat-msg-system{',
            'align-self:center;background:#f1f5f9;color:#64748b;',
            'font-size:11px;padding:6px 12px;border-radius:20px;',
            '}',
            '.wxkn-chat-msg-tool{',
            'font-size:11px;color:#64748b;margin-top:4px;display:block;',
            '}',
            '',
            '.wxkn-chat-footer{',
            'padding:12px 16px;border-top:1px solid #e2e8f0;',
            'display:flex;gap:8px;align-items:flex-end;flex-shrink:0;',
            '}',
            '.wxkn-chat-input{',
            'flex:1;border:1px solid #cbd5e1;border-radius:8px;',
            'padding:8px 12px;font-size:13px;outline:none;resize:none;',
            'font-family:inherit;max-height:80px;min-height:34px;',
            'line-height:1.4;',
            '}',
            '.wxkn-chat-input:focus{border-color:#2563eb;}',
            '.wxkn-chat-send{',
            'background:#2563eb;color:#fff;border:none;border-radius:8px;',
            'padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;',
            'white-space:nowrap;',
            '}',
            '.wxkn-chat-send:hover:not(:disabled){background:#1d4ed8;}',
            '.wxkn-chat-send:disabled{opacity:.5;cursor:not-allowed;}',
            '.wxkn-chat-clear{',
            'background:none;border:none;color:#94a3b8;cursor:pointer;',
            'font-size:11px;padding:4px 8px;white-space:nowrap;',
            '}',
            '.wxkn-chat-clear:hover{color:#ef4444;}',
            '',
            '.wxkn-chat-loading{text-align:center;padding:12px;color:#64748b;font-size:12px;}',
            '.wxkn-chat-loading-dot{',
            'display:inline-block;width:6px;height:6px;',
            'background:#94a3b8;border-radius:50%;margin:0 2px;',
            'animation:wxkn-bounce 1.4s infinite both;',
            '}',
            '.wxkn-chat-loading-dot:nth-child(2){animation-delay:-0.16s;}',
            '.wxkn-chat-loading-dot:nth-child(3){animation-delay:-0.32s;}',
            '@keyframes wxkn-bounce{',
            '0%,80%,100%{transform:scale(0);}40%{transform:scale(1);}',
            '}',

            '.wxkn-chat-msg-ai h1,.wxkn-chat-msg-ai h2,.wxkn-chat-msg-ai h3,',
            '.wxkn-chat-msg-ai h4,.wxkn-chat-msg-ai h5,.wxkn-chat-msg-ai h6,',
            '.wxkn-chat-msg-assistant h1,.wxkn-chat-msg-assistant h2,.wxkn-chat-msg-assistant h3,',
            '.wxkn-chat-msg-assistant h4,.wxkn-chat-msg-assistant h5,.wxkn-chat-msg-assistant h6{',
            'margin:8px 0 4px;font-size:14px;font-weight:600;line-height:1.3;',
            '}',
            '.wxkn-chat-msg-ai p,.wxkn-chat-msg-assistant p{margin:4px 0;}',
            '.wxkn-chat-msg-ai ul,.wxkn-chat-msg-ai ol,',
            '.wxkn-chat-msg-assistant ul,.wxkn-chat-msg-assistant ol{margin:4px 0;padding-left:20px;}',
            '.wxkn-chat-msg-ai li,.wxkn-chat-msg-assistant li{margin:2px 0;line-height:1.5;}',
            '.wxkn-chat-msg-ai blockquote,.wxkn-chat-msg-assistant blockquote{',
            'margin:8px 0;padding:8px 12px;border-left:4px solid #2563eb;',
            'color:#475569;background:#eff6ff;border-radius:0 6px 6px 0;',
            'font-style:italic;',
            '}',
            '.wxkn-chat-msg-ai code,.wxkn-chat-msg-assistant code{',
            'background:#e2e8f0;padding:2px 6px;border-radius:4px;',
            'font-size:12px;font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;',
            'color:#be123c;',
            '}',
            '.wxkn-chat-msg-ai pre,.wxkn-chat-msg-assistant pre{',
            'margin:8px 0;padding:12px 14px;background:#0f172a;color:#e2e8f0;',
            'border-radius:8px;overflow-x:auto;font-size:12px;',
            'font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;',
            'line-height:1.6;border:1px solid #334155;',
            '}',
            '.wxkn-chat-msg-ai pre code,.wxkn-chat-msg-assistant pre code{',
            'background:none;padding:0;color:inherit;font-size:inherit;',
            '}',
            '.wxkn-chat-msg-ai table,.wxkn-chat-msg-assistant table{',
            'width:100%;border-collapse:collapse;margin:8px 0;font-size:12px;',
            'border:1px solid #cbd5e1;border-radius:6px;overflow:hidden;',
            '}',
            '.wxkn-chat-msg-ai th,.wxkn-chat-msg-ai td,',
            '.wxkn-chat-msg-assistant th,.wxkn-chat-msg-assistant td{',
            'border:1px solid #cbd5e1;padding:7px 10px;text-align:left;',
            '}',
            '.wxkn-chat-msg-ai th,.wxkn-chat-msg-assistant th{',
            'background:#e2e8f0;font-weight:600;color:#334155;',
            '}',
            '.wxkn-chat-msg-ai tr:nth-child(even),.wxkn-chat-msg-assistant tr:nth-child(even){',
            'background:#f8fafc;',
            '}',
            '.wxkn-chat-msg-ai tr:hover,.wxkn-chat-msg-assistant tr:hover{',
            'background:#f1f5f9;',
            '}',
            '.wxkn-chat-msg-ai a,.wxkn-chat-msg-assistant a{color:#2563eb;text-decoration:underline;}',
            '.wxkn-chat-msg-ai hr,.wxkn-chat-msg-assistant hr{border:none;border-top:1px solid #e2e8f0;margin:8px 0;}',
            '.wxkn-step-list{display:flex;flex-direction:column;gap:6px;margin:4px 0;}',
            '.wxkn-step{padding:8px 12px;border-radius:8px;border-left:3px solid #94a3b8;background:#f8fafc;font-size:11.5px;display:flex;align-items:center;gap:8px;}',
            '.wxkn-step-status{flex-shrink:0;width:16px;text-align:center;}',
            '.wxkn-step-body{flex:1;min-width:0;}',
            '.wxkn-step--thinking{border-color:#8b5cf6;background:#f5f3ff;}',
            '.wxkn-step--running{border-color:#2563eb;background:#eff6ff;}',
            '.wxkn-step--success{border-color:#16a34a;background:#f0fdf4;}',
            '.wxkn-step--error{border-color:#dc2626;background:#fef2f2;}',
            '.wxkn-step-thinking-text{font-family:SFMono-Regular,Consolas,monospace;font-size:11px;color:#6b7280;line-height:1.5;white-space:pre-wrap;margin-top:4px;padding:6px 8px;background:#ede9fe;border-radius:4px;}',
            '@keyframes wxkn-step-pulse{0%,80%,100%{opacity:.4}40%{opacity:1}}',
            '.wxkn-step-thinking-dots span{display:inline-block;width:4px;height:4px;background:#8b5cf6;border-radius:50%;margin:0 2px;animation:wxkn-step-pulse 1.4s infinite both;}',
            '.wxkn-step-thinking-dots span:nth-child(2){animation-delay:-.16s;}',
            '.wxkn-step-thinking-dots span:nth-child(3){animation-delay:-.32s;}',
            '',
            '/* --- History Panel --- */',
            '.wxkn-history-panel{',
            'position:fixed;z-index:999998;',
            'width:380px;height:520px;',
            'background:#fff;border-radius:12px;',
            'box-shadow:0 8px 32px rgba(0,0,0,.2);',
            'display:flex;flex-direction:column;overflow:hidden;',
            'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;',
            '}',
            '.wxkn-history-header{',
            'display:flex;align-items:center;gap:10px;',
            'padding:12px 16px;background:#1e293b;color:#fff;',
            'border-bottom:1px solid #334155;flex-shrink:0;',
            '}',
            '.wxkn-history-header-title{font-size:14px;font-weight:600;}',
            '.wxkn-history-back{',
            'background:none;border:none;color:#94a3b8;cursor:pointer;',
            'font-size:16px;padding:2px 6px;line-height:1;',
            '}',
            '.wxkn-history-back:hover{color:#fff;}',
            '.wxkn-history-body{flex:1;overflow-y:auto;padding:12px 16px;display:flex;flex-direction:column;gap:10px;background:#f8fafc;}',
            '.wxkn-history-target-select{',
            'width:100%;padding:8px 10px;border:1px solid #cbd5e1;border-radius:6px;',
            'font-size:13px;background:#fff;cursor:pointer;outline:none;',
            '}',
            '.wxkn-history-target-select:focus{border-color:#2563eb;}',
            '.wxkn-history-version-list{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:6px;}',
            '.wxkn-history-version-item{',
            'padding:10px 12px;border:1px solid #e2e8f0;border-radius:8px;',
            'background:#fff;cursor:pointer;transition:border-color .15s;',
            '}',
            '.wxkn-history-version-item:hover{border-color:#94a3b8;}',
            '.wxkn-history-version-item.active{border-color:#2563eb;border-width:2px;background:#eff6ff;}',
            '.wxkn-history-version-ts{font-size:11px;color:#64748b;margin-bottom:2px;}',
            '.wxkn-history-version-prompt{font-size:12px;color:#1e293b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:2px;}',
            '.wxkn-history-version-meta{font-size:11px;color:#94a3b8;}',
            '.wxkn-history-preview-area{display:flex;flex-direction:column;gap:6px;}',
            '.wxkn-history-preview-textarea{',
            'width:100%;height:180px;padding:10px;border:1px solid #e2e8f0;border-radius:6px;',
            'font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;',
            'font-size:11px;line-height:1.5;resize:vertical;background:#0f172a;color:#e2e8f0;',
            '}',
            '.wxkn-history-footer{padding:12px 16px;border-top:1px solid #e2e8f0;flex-shrink:0;}',
            '.wxkn-history-restore-btn{',
            'width:100%;padding:10px;background:#dc2626;color:#fff;border:none;border-radius:8px;',
            'font-size:13px;font-weight:600;cursor:pointer;',
            '}',
            '.wxkn-history-restore-btn:hover:not(:disabled){background:#b91c1c;}',
            '.wxkn-history-restore-btn:disabled{background:#94a3b8;cursor:not-allowed;opacity:.6;}',
            '.wxkn-history-empty{text-align:center;color:#94a3b8;font-size:13px;padding:24px 0;}',
            '',
            '/* --- Confirm Dialog --- */',
            '.wxkn-confirm-overlay{',
            'position:fixed;top:0;left:0;right:0;bottom:0;',
            'background:rgba(0,0,0,.5);z-index:9999999;',
            'display:flex;align-items:center;justify-content:center;',
            '}',
            '.wxkn-confirm-dialog{',
            'background:#fff;border-radius:12px;padding:24px;max-width:400px;width:90%;',
            'box-shadow:0 8px 32px rgba(0,0,0,.3);',
            '}',
            '.wxkn-confirm-title{font-size:16px;font-weight:600;color:#1e293b;margin-bottom:12px;}',
            '.wxkn-confirm-message{font-size:13px;color:#475569;line-height:1.6;margin-bottom:20px;}',
            '.wxkn-confirm-actions{display:flex;gap:10px;justify-content:flex-end;}',
            '.wxkn-confirm-btn-cancel{',
            'padding:8px 16px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;',
            'font-size:13px;cursor:pointer;color:#475569;',
            '}',
            '.wxkn-confirm-btn-cancel:hover{background:#f1f5f9;}',
            '.wxkn-confirm-btn-ok{',
            'padding:8px 16px;border:none;border-radius:8px;background:#dc2626;',
            'font-size:13px;cursor:pointer;color:#fff;font-weight:600;',
            '}',
            '.wxkn-confirm-btn-ok:hover{background:#b91c1c;}',
            '',
            '/* --- FAB Menu --- */',
            '.wxkn-chat-fab-wrap{position:fixed;bottom:24px;right:24px;z-index:999999;}',
            '.wxkn-fab-menu{',
            'position:absolute;bottom:64px;right:0;',
            'background:#fff;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.2);',
            'overflow:hidden;display:none;min-width:160px;',
            '}',
            '.wxkn-fab-menu-item{',
            'display:block;width:100%;padding:10px 14px;border:none;background:none;',
            'font-size:13px;cursor:pointer;text-align:left;color:#1e293b;',
            '}',
            '.wxkn-fab-menu-item:hover{background:#f1f5f9;}',
            '',
            '/* --- Publish Button --- */',
            '.wxkn-publish-bar{',
            'display:flex;align-items:center;gap:10px;',
            'padding:10px 16px;background:#f0fdf4;border-top:1px solid #bbf7d0;',
            'font-size:12px;color:#166534;',
            '}',
            '.wxkn-publish-btn{',
            'padding:6px 14px;background:#16a34a;color:#fff;border:none;border-radius:6px;',
            'font-size:12px;font-weight:600;cursor:pointer;',
            '}',
            '.wxkn-publish-btn:hover{background:#15803d;}',
            '.wxkn-publish-btn:disabled{opacity:.5;cursor:not-allowed;background:#94a3b8;}',

            '/* --- Inline Edit Toolbar --- */',
            '.wxkn-inline-toolbar{',
            'position:fixed;z-index:999997;',
            'background:#fff;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.25);',
            'display:flex;align-items:center;gap:2px;padding:4px;',
            'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;',
            '}',
            '.wxkn-inline-toolbar-btn{',
            'padding:6px 10px;border:none;border-radius:6px;background:none;',
            'font-size:12px;cursor:pointer;color:#475569;white-space:nowrap;',
            'transition:background .15s,color .15s;',
            '}',
            '.wxkn-inline-toolbar-btn:hover{background:#f1f5f9;color:#1e293b;}',
            '.wxkn-inline-toolbar-btn[data-action="rewrite"]:hover{background:#eff6ff;color:#2563eb;}',
            '.wxkn-inline-toolbar-btn[data-action="polish"]:hover{background:#f5f3ff;color:#8b5cf6;}',
            '.wxkn-inline-toolbar-btn[data-action="translate"]:hover{background:#ecfdf5;color:#10b981;}',
            '.wxkn-inline-toolbar-btn[data-action="summarize"]:hover{background:#fef3c7;color:#d97706;}',
            '.wxkn-inline-toolbar-btn[data-action="edit"]:hover{background:#e0e7ff;color:#4f46e5;}',
            '.wxkn-inline-toolbar-btn[data-action="custom"]:hover{background:#fee2e2;color:#dc2626;}',
            '.wxkn-inline-toolbar-divider{width:1px;height:20px;background:#e2e8f0;margin:2px 4px;}',
            '',
            '/* --- Inline Preview Dialog --- */',
            '.wxkn-inline-preview-overlay{',
            'position:fixed;top:0;left:0;right:0;bottom:0;',
            'background:rgba(0,0,0,.5);z-index:9999998;',
            'display:flex;align-items:center;justify-content:center;',
            '}',
            '.wxkn-inline-preview-dialog{',
            'background:#fff;border-radius:12px;max-width:700px;width:90%;',
            'box-shadow:0 8px 32px rgba(0,0,0,.3);overflow:hidden;',
            '}',
            '.wxkn-inline-preview-header{',
            'padding:12px 16px;background:#1e293b;color:#fff;font-size:14px;font-weight:600;',
            '}',
            '.wxkn-inline-preview-body{padding:16px;display:flex;gap:16px;}',
            '.wxkn-inline-preview-pane{flex:1;min-width:0;}',
            '.wxkn-inline-preview-pane-label{',
            'font-size:11px;font-weight:600;color:#64748b;margin-bottom:8px;',
            '}',
            '.wxkn-inline-preview-pane-content{',
            'padding:12px;border-radius:8px;font-size:13px;line-height:1.6;',
            'white-space:pre-wrap;word-break:break-word;max-height:300px;overflow-y:auto;',
            '}',
            '.wxkn-inline-preview-pane-original{background:#fef2f2;color:#991b1b;}',
            '.wxkn-inline-preview-pane-new{background:#f0fdf4;color:#166534;}',
            '.wxkn-inline-preview-footer{',
            'padding:12px 16px;border-top:1px solid #e2e8f0;',
            'display:flex;gap:10px;justify-content:flex-end;',
            '}',
            '.wxkn-inline-preview-btn-accept{',
            'padding:8px 20px;border:none;border-radius:8px;background:#16a34a;',
            'font-size:13px;font-weight:600;cursor:pointer;color:#fff;',
            '}',
            '.wxkn-inline-preview-btn-accept:hover{background:#15803d;}',
            '.wxkn-inline-preview-btn-reject{',
            'padding:8px 20px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;',
            'font-size:13px;cursor:pointer;color:#475569;',
            '}',
            '.wxkn-inline-preview-btn-reject:hover{background:#f1f5f9;}',
            '',
            '/* --- Inline Custom Prompt Modal --- */',
            '.wxkn-inline-custom-modal{',
            'position:fixed;top:0;left:0;right:0;bottom:0;',
            'background:rgba(0,0,0,.5);z-index:9999999;',
            'display:flex;align-items:center;justify-content:center;',
            '}',
            '.wxkn-inline-custom-dialog{',
            'background:#fff;border-radius:12px;padding:20px;max-width:400px;width:90%;',
            'box-shadow:0 8px 32px rgba(0,0,0,.3);',
            '}',
            '.wxkn-inline-custom-title{font-size:14px;font-weight:600;color:#1e293b;margin-bottom:12px;}',
            '.wxkn-inline-custom-textarea{',
            'width:100%;height:100px;padding:10px;border:1px solid #cbd5e1;border-radius:8px;',
            'font-size:13px;resize:vertical;outline:none;font-family:inherit;',
            '}',
            '.wxkn-inline-custom-textarea:focus{border-color:#2563eb;}',
            '.wxkn-inline-custom-footer{margin-top:16px;display:flex;gap:10px;justify-content:flex-end;}',
            '.wxkn-inline-custom-btn-cancel{',
            'padding:8px 16px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;',
            'font-size:13px;cursor:pointer;color:#475569;',
            '}',
            '.wxkn-inline-custom-btn-cancel:hover{background:#f1f5f9;}',
            '.wxkn-inline-custom-btn-send{',
            'padding:8px 16px;border:none;border-radius:8px;background:#2563eb;',
            'font-size:13px;font-weight:600;cursor:pointer;color:#fff;',
            '}',
            '.wxkn-inline-custom-btn-send:hover{background:#1d4ed8;}',
            '.wxkn-inline-custom-btn-send:disabled{opacity:.5;cursor:not-allowed;}',
            '',
            '/* --- Inline Processing Indicator --- */',
            '.wxkn-inline-processing{',
            'position:fixed;z-index:999997;',
            'background:#fff;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.25);',
            'padding:10px 14px;font-size:13px;color:#475569;',
            'display:flex;align-items:center;gap:8px;',
            '}',
            '.wxkn-inline-processing-spinner{',
            'width:16px;height:16px;border:2px solid #e2e8f0;border-top-color:#2563eb;',
            'border-radius:50%;animation:wxkn-spin 1s linear infinite;',
            '}',
            '@keyframes wxkn-spin{to{transform:rotate(360deg)}}',

            '/* --- Inline Edit Mode --- */',
            '.wxkn-inline-edit-overlay{',
            'position:fixed;z-index:999996;',
            'background:#fff;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.25);',
            'padding:8px;',
            '}',
            '.wxkn-inline-edit-textarea{',
            'width:100%;min-width:200px;max-width:400px;',
            'min-height:60px;max-height:200px;',
            'padding:8px;border:1px solid #cbd5e1;border-radius:6px;',
            'font-size:14px;line-height:1.5;resize:both;',
            'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;',
            'outline:none;',
            '}',
            '.wxkn-inline-edit-textarea:focus{border-color:#4f46e5;}',
            '.wxkn-inline-edit-footer{',
            'display:flex;gap:6px;justify-content:flex-end;margin-top:6px;',
            '}',
            '.wxkn-inline-edit-btn-save{',
            'padding:6px 14px;border:none;border-radius:6px;background:#4f46e5;',
            'font-size:12px;font-weight:600;cursor:pointer;color:#fff;',
            '}',
            '.wxkn-inline-edit-btn-save:hover{background:#4338ca;}',
            '.wxkn-inline-edit-btn-cancel{',
            'padding:6px 14px;border:1px solid #e2e8f0;border-radius:6px;background:#fff;',
            'font-size:12px;cursor:pointer;color:#475569;',
            '}',
            '.wxkn-inline-edit-btn-cancel:hover{background:#f1f5f9;}',
        ].join('\n');

        var style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
    }

    /* ========================================================================
     * 4. UTILITY FUNCTIONS
     * ======================================================================== */

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    var md = window.markdownit ? window.markdownit({ html: false, linkify: true, typographer: true }) : null;

    /* ========================================================================
     * 5. POSITION MANAGEMENT (localStorage)
     * ======================================================================== */

    function savePosition() {
        try {
            localStorage.setItem(CONFIG.storageKeyPos, JSON.stringify(state.position));
        } catch (e) {
            // Storage full or unavailable -- silently ignore
        }
    }

    function loadPosition() {
        try {
            var raw = localStorage.getItem(CONFIG.storageKeyPos);
            if (raw) {
                var parsed = JSON.parse(raw);
                if (parsed && typeof parsed.x === 'number' && typeof parsed.y === 'number') {
                    state.position = parsed;
                }
            }
        } catch (e) {
            // Corrupted data -- use defaults
        }
    }

    function applyPosition() {
        applyPositionTo(widget);
        if (historyPanel && state.mode === 'history') {
            applyPositionTo(historyPanel);
        }
    }

    function constrainPosition() {
        if (!widget) return;
        var maxX = window.innerWidth - widget.offsetWidth;
        var maxY = window.innerHeight - widget.offsetHeight;
        state.position.x = Math.max(0, Math.min(state.position.x, maxX));
        state.position.y = Math.max(0, Math.min(state.position.y, maxY));
        applyPosition();
    }

    /* ========================================================================
     * 6. HISTORY MANAGEMENT (localStorage)
     * ======================================================================== */

    function saveHistory() {
        try {
            if (state.history.length > 50) {
                state.history = state.history.slice(state.history.length - 50);
            }
            localStorage.setItem(CONFIG.storageKeyHistory(CONFIG.postId), JSON.stringify(state.history));
        } catch (e) {
            // Silently ignore
        }
    }

    function loadHistory() {
        try {
            var raw = localStorage.getItem(CONFIG.storageKeyHistory(CONFIG.postId));
            if (raw) {
                var parsed = JSON.parse(raw);
                if (Array.isArray(parsed)) {
                    state.history = parsed;
                }
            }
        } catch (e) {
            // Use empty history
        }
    }

    function appendMessage(role, content, toolsUsed) {
        var msgDiv = document.createElement('div');

        var roleClass = 'wxkn-chat-msg-' + role;
        msgDiv.className = 'wxkn-chat-msg ' + roleClass;

        if (role === 'system') {
            msgDiv.textContent = content;
        } else if (role === 'assistant' && md) {
            msgDiv.innerHTML = md.render(content);
        } else {
            msgDiv.innerHTML = escapeHtml(content);
        }

        if (toolsUsed && toolsUsed.length > 0) {
            var toolSpan = document.createElement('span');
            toolSpan.className = 'wxkn-chat-msg-tool';
            toolSpan.textContent = '使用工具: ' + (Array.isArray(toolsUsed) ? toolsUsed.map(function(t) { return typeof t === 'string' ? t : (t.name || t); }) : []).join(', ');
            msgDiv.appendChild(toolSpan);
        }

        bodyEl.appendChild(msgDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        if (bodyEl) {
            // Use setTimeout to ensure DOM is fully rendered before scrolling
            setTimeout(function() {
                bodyEl.scrollTop = bodyEl.scrollHeight;
            }, 100);
        }
    }

    function renderMessages() {
        if (!bodyEl) return;

        bodyEl.innerHTML = '';

        if (state.history.length === 0) {
            appendMessage('system', '你好！我是 WXKN AI 助手，有什么可以帮助你的？');
        } else {
            for (var i = 0; i < state.history.length; i++) {
                var entry = state.history[i];
                appendMessage(entry.role, entry.content, entry.tools_used);
            }
        }

        scrollToBottom();
    }

    function clearConversation() {
        showConfirmDialog(
            '清空对话',
            '确定要清空对话历史吗？\n\n此操作无法撤销。',
            function() {
                state.history = [];
                saveHistory();
                renderMessages();
            }
        );
    }

    /* ========================================================================
     * 6b. STEP CARD DOM FUNCTIONS
     * ======================================================================== */

    function createStepListElement() {
        var el = document.createElement('div');
        el.className = 'wxkn-step-list';
        return el;
    }

    function updateOrCreateStepCard(container, stepNum, status, content, elapsed) {
        var card = container.querySelector('[data-step="' + stepNum + '"]');
        if (!card) {
            card = document.createElement('div');
            card.className = 'wxkn-step wxkn-step--' + status;
            card.setAttribute('data-step', stepNum);
            card.innerHTML =
                '<span class="wxkn-step-status"></span>' +
                '<span class="wxkn-step-body"></span>' +
                '<span class="wxkn-step-time"></span>';
            container.appendChild(card);
            scrollToBottom();
        } else {
            card.className = 'wxkn-step wxkn-step--' + status;
        }

        var statusEl = card.querySelector('.wxkn-step-status');
        var bodyEl = card.querySelector('.wxkn-step-body');
        var timeEl = card.querySelector('.wxkn-step-time');

        if (elapsed !== undefined && timeEl) {
            timeEl.textContent = elapsed + 's';
            timeEl.style.cssText = 'flex-shrink:0;font-size:10px;color:#94a3b8;margin-left:auto;';
        }

        switch (status) {
            case 'thinking':
                if (content) {
                    statusEl.innerHTML = '<i class="fa-solid fa-check" style="color:#8b5cf6;font-size:10px"></i>';
                    bodyEl.innerHTML = '<div class="wxkn-step-thinking-text">' + escapeHtml(content) + '</div>';
                } else {
                    statusEl.innerHTML = '<span class="wxkn-step-thinking-dots"><span></span><span></span><span></span></span>';
                    bodyEl.textContent = '思考中...';
                }
                break;
            case 'running':
                statusEl.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="color:#2563eb;font-size:10px"></i>';
                bodyEl.textContent = content;
                break;
        }
    }

    function updateStepResult(container, stepNum, ok, errorMsg, elapsed) {
        var card = container.querySelector('[data-step="' + stepNum + '"]');
        if (!card) return;

        card.className = 'wxkn-step wxkn-step--' + (ok ? 'success' : 'error');
        var statusEl = card.querySelector('.wxkn-step-status');

        if (ok) {
            statusEl.innerHTML = '<i class="fa-solid fa-check" style="color:#16a34a;font-size:10px"></i>';
        } else {
            statusEl.innerHTML = '<i class="fa-solid fa-xmark" style="color:#dc2626;font-size:10px"></i>';
            var bodyEl = card.querySelector('.wxkn-step-body');
            if (errorMsg) {
                bodyEl.innerHTML += '<div style="color:#dc2626;margin-top:2px;font-size:10px">' + escapeHtml(errorMsg) + '</div>';
            }
        }

        var timeEl = card.querySelector('.wxkn-step-time');
        if (elapsed !== undefined && timeEl) {
            timeEl.textContent = elapsed + 's';
        }
    }

    function updateStepText(container, stepNum, text, elapsed) {
        var card = container.querySelector('[data-step="' + stepNum + '"]');
        if (!card) return;

        var bodyEl = card.querySelector('.wxkn-step-body');
        if (bodyEl) {
            bodyEl.textContent = text;
        }

        var timeEl = card.querySelector('.wxkn-step-time');
        if (elapsed !== undefined && timeEl) {
            timeEl.textContent = elapsed + 's';
        }
    }

    function markStepComplete(container, stepNum) {
        var card = container.querySelector('[data-step="' + stepNum + '"]');
        if (card) {
            var statusEl = card.querySelector('.wxkn-step-status');
            if (statusEl && !statusEl.querySelector('.fa-check')) {
                statusEl.innerHTML = '<i class="fa-solid fa-check" style="color:#8b5cf6;font-size:10px"></i>';
            }
        }
    }

    /* ========================================================================
     * 6c. SSE EVENT HANDLER & PARSER
     * ======================================================================== */

    function handleSSEEvent(eventType, rawData) {
        console.log('[DEBUG] handleSSEEvent called:', eventType);
        var data;
        try { data = JSON.parse(rawData); } catch(e) { return; }

        switch (eventType) {
            case 'thinking':
                console.log('[DEBUG] processing thinking event');
                if (data.text) {
                    updateOrCreateStepCard(state.stepListEl, data.step, 'thinking', data.text, data.elapsed);
                }
                break;
            case 'thinking_end':
                console.log('[DEBUG] processing thinking_end event');
                markStepComplete(state.stepListEl, data.step);
                break;
            case 'tool_call':
                var toolText = data.label || data.name;
                if (data.status === 'pending') {
                    toolText = '准备调用: ' + toolText;
                }
                updateOrCreateStepCard(state.stepListEl, data.step, 'running', toolText, data.elapsed);
                break;
            case 'tool_executing':
                // Update existing card to show "executing" state
                updateStepText(state.stepListEl, data.step, '执行中: ' + (data.label || data.name), data.elapsed);
                break;
            case 'tool_result':
                updateStepResult(state.stepListEl, data.step, data.ok, data.error, data.elapsed);
                // Don't show draft saved message here, wait for done event
                break;
            case 'content':
                break;
            case 'done':
                console.log('[DEBUG] done event received:', data);
                hideLoading();
                // Remove step list and add message with small delay to ensure proper DOM ordering
                setTimeout(function() {
                    console.log('[DEBUG] Processing done event in setTimeout');
                    if (state.stepListEl && state.stepListEl.parentNode) {
                        state.stepListEl.parentNode.removeChild(state.stepListEl);
                        state.stepListEl = null;
                    }
                    // Add assistant message after step list is removed
                    appendMessage('assistant', data.reply, data.tools_used);
                    state.history.push({
                        role: 'assistant',
                        content: data.reply,
                        timestamp: Date.now(),
                        tools_used: data.tools_used,
                    });
                    saveHistory();
                    if (data.draft_updated) {
                        // Show publish bar instead of auto-refresh
                        showPublishBar();
                    }
                }, 50);
                break;
            case 'error':
                hideLoading();
                appendMessage('system', '错误: ' + (data.message || '未知错误'));
                break;
        }
    }

    function createSSEParser() {
        return {
            lineBuffer: '',
            eventType: '',
            eventData: '',
        };
    }

    function flushSSEEvent(parser, events) {
        if (!parser.eventType || parser.eventData === '') {
            return;
        }

        var eventData = parser.eventData;
        if (eventData.charAt(eventData.length - 1) === '\n') {
            eventData = eventData.slice(0, -1);
        }

        events.push({ type: parser.eventType, data: eventData });
        parser.eventType = '';
        parser.eventData = '';
    }

    function parseSSEChunk(chunk, parser, isFinal) {
        var events = [];
        parser.lineBuffer += chunk;

        var normalized = parser.lineBuffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        var lines = normalized.split('\n');

        if (!isFinal) {
            parser.lineBuffer = lines.pop() || '';
        } else {
            parser.lineBuffer = '';
        }

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];

            if (line === '') {
                flushSSEEvent(parser, events);
                continue;
            }

            if (line.charAt(0) === ':') {
                continue;
            }

            if (line.startsWith('event:')) {
                parser.eventType = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
                parser.eventData += line.substring(5).replace(/^ /, '') + '\n';
            }
        }

        if (isFinal) {
            flushSSEEvent(parser, events);
        }

        return events;
    }

    /* ========================================================================
     * 7. LOADING INDICATOR
     * ======================================================================== */

    function showLoading() {
        hideLoading(); // Remove any existing loading indicator first

        var loader = document.createElement('div');
        loader.id = 'wxkn-loading';
        loader.className = 'wxkn-chat-loading';

        for (var i = 0; i < 3; i++) {
            var dot = document.createElement('span');
            dot.className = 'wxkn-chat-loading-dot';
            loader.appendChild(dot);
        }

        bodyEl.appendChild(loader);
        scrollToBottom();
    }

    function hideLoading() {
        var existing = document.getElementById('wxkn-loading');
        if (existing && existing.parentNode) {
            existing.parentNode.removeChild(existing);
        }
    }

    /* ========================================================================
     * 8. WIDGET TOGGLE
     * ======================================================================== */

    function expandWidget() {
        if (fab) fab.style.display = 'none';
        if (widget) {
            widget.style.display = 'flex';
            applyPosition();
            constrainPosition();
        }
        state.expanded = true;
        if (inputEl) inputEl.focus();
    }

    function minimizeWidget() {
        if (widget) widget.style.display = 'none';
        if (fab) fab.style.display = '';
        state.expanded = false;
    }

    function toggleWidget() {
        if (state.expanded) {
            minimizeWidget();
        } else {
            expandWidget();
        }
    }

    function closeWidget() {
        minimizeWidget();
    }

    /* ========================================================================
     * 9. SEND MESSAGE (async)
     * ======================================================================== */

    async function sendMessage() {
        if (state.sending) return;

        var text = (inputEl.value || '').trim();
        if (!text) return;

        // Remove any existing step list from previous request
        if (state.stepListEl && state.stepListEl.parentNode) {
            state.stepListEl.parentNode.removeChild(state.stepListEl);
            state.stepListEl = null;
        }
        // Also clean up any orphaned step lists
        var existingStepList = bodyEl.querySelector('.wxkn-step-list');
        if (existingStepList) {
            existingStepList.parentNode.removeChild(existingStepList);
        }

        // Append user message
        state.history.push({
            role: 'user',
            content: text,
            timestamp: Date.now(),
        });
        saveHistory();
        renderMessages();

        inputEl.value = '';
        inputEl.style.height = '';

        state.sending = true;
        sendBtn.disabled = true;

        // Create step list container
        state.stepListEl = createStepListElement();
        bodyEl.appendChild(state.stepListEl);
        showLoading();

        // Build history for backend
        var historyForBackend = [];
        for (var i = 0; i < state.history.length - 1; i++) {
            var entry = state.history[i];
            historyForBackend.push([entry.role, entry.content]);
        }

        var params = new URLSearchParams();
        params.append('action', 'wxkn_preview_chat_stream');
        params.append('_wpnonce', CONFIG.nonce);
        params.append('post_id', CONFIG.postId);
        params.append('message', text);
        params.append('history', JSON.stringify(historyForBackend));

        try {
            var response = await fetch(CONFIG.streamUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'text/event-stream',
                },
                body: params.toString(),
            });

            if (!response.ok) {
                hideLoading();
                appendMessage('system', '服务器错误 (HTTP ' + response.status + ')，请重试。');
                return;
            }

            // Fallback: if ReadableStream not supported, re-request with sync endpoint
            if (!response.body || typeof response.body.getReader !== 'function') {
                params.set('action', 'wxkn_preview_chat');
                var syncResp = await fetch(CONFIG.ajaxUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: params.toString(),
                });
                var result = await syncResp.json();
                hideLoading();
                if (result.success && result.data) {
                    var d = result.data;
                    state.history.push({
                        role: 'assistant',
                        content: d.reply,
                        timestamp: Date.now(),
                        tools_used: d.tools_used || undefined,
                    });
                    saveHistory();
                    renderMessages();
                    if (d.draft_updated === true) {
                        // Show publish bar instead of auto-refresh
                        showPublishBar();
                    }
                } else {
                    appendMessage('system', '错误: ' + ((result.data && result.data.message) || '未知错误'));
                }
                return;
            }

            // Stream reading
            var reader = response.body.getReader();
            var decoder = new TextDecoder();
            var parser = createSSEParser();

            while (true) {
                var _ref = await reader.read();
                var done = _ref.done;
                var value = _ref.value;

                var chunkText = value ? decoder.decode(value, { stream: !done }) : '';
                if (done) {
                    chunkText += decoder.decode();
                }

                var events = parseSSEChunk(chunkText, parser, done);
                for (var eIdx = 0; eIdx < events.length; eIdx++) {
                    handleSSEEvent(events[eIdx].type, events[eIdx].data);
                }

                if (done) {
                    break;
                }

                // Yield to browser so it can render DOM updates incrementally
                await new Promise(function (r) { return setTimeout(r, 0); });
            }
        } catch (err) {
            hideLoading();
            appendMessage('system', '网络错误：无法连接服务器。');
        } finally {
            state.sending = false;
            sendBtn.disabled = false;
        }
    }

    /* ========================================================================
     * 10. DRAG BEHAVIOR
     * ======================================================================== */

    function onDragStart(e) {
        // Skip if clicking a header button
        if (e.target.closest('.wxkn-chat-header-btn')) return;

        e.preventDefault();
        state.dragging = true;

        var rect = widget.getBoundingClientRect();
        state.dragOffsetX = e.clientX - rect.left;
        state.dragOffsetY = e.clientY - rect.top;
    }

    function onDragMove(e) {
        if (!state.dragging) return;

        state.position.x = e.clientX - state.dragOffsetX;
        state.position.y = e.clientY - state.dragOffsetY;
        applyPosition();
    }

    function onDragEnd() {
        if (!state.dragging) return;

        state.dragging = false;
        constrainPosition();
        savePosition();
    }

    /* ========================================================================
     * 11. TEXTAREA AUTO-RESIZE
     * ======================================================================== */

    function autoResizeTextarea() {
        if (!inputEl) return;
        inputEl.style.height = 'auto';
        inputEl.style.height = Math.min(inputEl.scrollHeight, 80) + 'px';
    }

    /* ========================================================================
     * 11b. HISTORY PANEL
     * ======================================================================== */

    function toggleFabMenu(e) {
        e.stopPropagation();
        var visible = fabMenu.style.display !== 'none';
        fabMenu.style.display = visible ? 'none' : 'block';
    }

    function switchMode(mode) {
        state.mode = mode;
        fabMenu.style.display = 'none';
        if (mode === 'chat') {
            historyPanel.style.display = 'none';
            expandWidget();
        } else if (mode === 'history') {
            widget.style.display = 'none';
            fab.style.display = 'none';
            historyPanel.style.display = 'flex';
            applyPositionTo(historyPanel);
            constrainPosition();
            loadHistoryTargets();
        }
    }

    function applyPositionTo(el) {
        if (!el) return;
        el.style.left = state.position.x + 'px';
        el.style.top = state.position.y + 'px';
    }

    function loadHistoryTargets() {
        var params = new URLSearchParams();
        params.append('action', 'wxkn_backup_targets');
        params.append('_wpnonce', CONFIG.backupNonce || '');
        fetch(CONFIG.ajaxUrl, { method: 'POST', body: params })
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (!res.success || !res.data.targets) return;
                state.targets = res.data.targets;
                renderTargetSelect();
            })
            .catch(function (err) { console.error('[wxkn_history] load targets failed:', err); });
    }

    function renderTargetSelect() {
        var select = historyPanel.querySelector('.wxkn-history-target-select');
        select.innerHTML = '';
        if (state.targets.length === 0) {
            select.innerHTML = '<option value="">暂无备份</option>';
            return;
        }
        state.targets.forEach(function (t) {
            var opt = document.createElement('option');
            opt.value = JSON.stringify(t);
            opt.textContent = t.label;
            select.appendChild(opt);
            if (t.type === 'page' && t.id == CONFIG.postId) opt.selected = true;
        });
        onTargetChange();
        select.removeEventListener('change', onTargetChange);
        select.addEventListener('change', onTargetChange);
    }

    function onTargetChange() {
        var select = historyPanel.querySelector('.wxkn-history-target-select');
        if (!select.value) return;
        try { state.selectedTarget = JSON.parse(select.value); } catch(e) { return; }
        state.selectedVersion = null;
        state.previewContent = '';
        historyPanel.querySelector('.wxkn-history-preview-area').style.display = 'none';
        historyPanel.querySelector('.wxkn-history-restore-btn').disabled = true;
        loadVersionsForTarget(state.selectedTarget);
    }

    function loadVersionsForTarget(target) {
        var params = new URLSearchParams();
        params.append('action', 'wxkn_backup_list');
        params.append('_wpnonce', CONFIG.backupNonce || '');
        params.append('type', target.type);
        if (target.type === 'page') params.append('post_id', target.id);
        if (target.type === 'file') params.append('path', target.path);
        fetch(CONFIG.ajaxUrl, { method: 'POST', body: params })
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (!res.success) return;
                state.backups = res.data.backups || [];
                renderVersionList();
            })
            .catch(function (err) { console.error('[wxkn_history] load versions failed:', err); });
    }

    function renderVersionList() {
        var ul = historyPanel.querySelector('.wxkn-history-version-list');
        ul.innerHTML = '';
        if (state.backups.length === 0) {
            ul.innerHTML = '<li class="wxkn-history-empty">暂无版本记录</li>';
            return;
        }
        state.backups.forEach(function (b) {
            var li = document.createElement('li');
            li.className = 'wxkn-history-version-item';
            li.setAttribute('data-ts', b.ts);
            var d = new Date(b.ts);
            var timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' });
            li.innerHTML =
                '<div class="wxkn-history-version-ts">' + escapeHtml(timeStr) + '</div>' +
                (b.prompt ? '<div class="wxkn-history-version-prompt">"' + escapeHtml(b.prompt) + '"</div>' : '') +
                '<div class="wxkn-history-version-meta">' + escapeHtml(b.user_name || '') + ' - ' + formatSize(b.size) + '</div>';
            li.addEventListener('click', function() { selectVersion(b.ts); });
            ul.appendChild(li);
        });
    }

    function selectVersion(ts) {
        state.selectedVersion = ts;
        historyPanel.querySelectorAll('.wxkn-history-version-item').forEach(function (item) {
            item.classList.toggle('active', item.getAttribute('data-ts') === ts);
        });
        loadPreview(ts);
    }

    function loadPreview(ts) {
        var target = state.selectedTarget;
        if (!target) return;
        var params = new URLSearchParams();
        params.append('action', 'wxkn_backup_preview');
        params.append('_wpnonce', CONFIG.backupNonce || '');
        params.append('type', target.type);
        if (target.type === 'page') params.append('post_id', target.id);
        if (target.type === 'file') params.append('path', target.path);
        params.append('timestamp', ts);
        fetch(CONFIG.ajaxUrl, { method: 'POST', body: params })
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (!res.success || !res.data.content) return;
                state.previewContent = res.data.content;
                var previewArea = historyPanel.querySelector('.wxkn-history-preview-area');
                previewArea.querySelector('textarea').value = res.data.content;
                previewArea.style.display = 'block';
                historyPanel.querySelector('.wxkn-history-restore-btn').disabled = false;
            })
            .catch(function (err) { console.error('[wxkn_history] preview failed:', err); });
    }

    function confirmRestore() {
        var ts = state.selectedVersion;
        var target = state.selectedTarget;
        if (!ts || !target) return;
        var verInfo = state.backups.find(function (b) { return b.ts === ts; });
        if (!verInfo) return;
        showConfirmDialog(
            '确认恢复',
            '确定要恢复到此版本吗？\n\n时间: ' + new Date(ts).toLocaleString() +
            (verInfo.prompt ? '\nPrompt: "' + verInfo.prompt + '"' : ''),
            function() { doRestore(ts, target); }
        );
    }

    function doRestore(ts, target) {
        var params = new URLSearchParams();
        params.append('action', 'wxkn_backup_restore');
        params.append('_wpnonce', CONFIG.backupNonce || '');
        params.append('type', target.type);
        if (target.type === 'page') params.append('post_id', target.id);
        if (target.type === 'file') params.append('path', target.path);
        params.append('timestamp', ts);
        fetch(CONFIG.ajaxUrl, { method: 'POST', body: params })
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.data && res.data.conflict) {
                    showConfirmDialog(
                        '文件已修改',
                        '此文件自快照后已被修改，恢复将覆盖当前内容。是否继续？',
                        function() { forceRestore(ts, target); }
                    );
                } else if (res.success) {
                    alert('恢复成功！页面即将刷新。');
                    location.reload();
                } else {
                    alert('恢复失败: ' + ((res.data && res.data.message) || '未知错误'));
                }
            })
            .catch(function (err) { alert('错误: ' + err.message); });
    }

    function forceRestore(ts, target) {
        var params = new URLSearchParams();
        params.append('action', 'wxkn_backup_restore');
        params.append('_wpnonce', CONFIG.backupNonce || '');
        params.append('type', target.type);
        if (target.type === 'page') params.append('post_id', target.id);
        if (target.type === 'file') params.append('path', target.path);
        params.append('timestamp', ts);
        params.append('force', '1');
        fetch(CONFIG.ajaxUrl, { method: 'POST', body: params })
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.success) {
                    alert('恢复成功！页面即将刷新。');
                    location.reload();
                } else {
                    alert('恢复失败: ' + ((res.data && res.data.message) || '未知错误'));
                }
            })
            .catch(function (err) { alert('错误: ' + err.message); });
    }

    function showConfirmDialog(title, message, onOk) {
        var overlay = document.createElement('div');
        overlay.className = 'wxkn-confirm-overlay';
        overlay.innerHTML =
            '<div class="wxkn-confirm-dialog">' +
            '  <div class="wxkn-confirm-title">' + escapeHtml(title) + '</div>' +
            '  <div class="wxkn-confirm-message">' + escapeHtml(message).replace(/\n/g, '<br>') + '</div>' +
            '  <div class="wxkn-confirm-actions">' +
            '    <button class="wxkn-confirm-btn-cancel">取消</button>' +
            '    <button class="wxkn-confirm-btn-ok">确认</button>' +
            '  </div>' +
            '</div>';
        overlay.querySelector('.wxkn-confirm-btn-cancel').addEventListener('click', function() {
            document.body.removeChild(overlay);
        });
        overlay.querySelector('.wxkn-confirm-btn-ok').addEventListener('click', function() {
            document.body.removeChild(overlay);
            if (onOk) onOk();
        });
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) document.body.removeChild(overlay);
        });
        document.body.appendChild(overlay);
    }

    /* ========================================================================
     * 11d. PUBLISH FUNCTIONS
     * ======================================================================== */

    function showPublishBar() {
        // Remove existing publish bar first
        var existingBar = document.querySelector('.wxkn-publish-bar');
        if (existingBar) {
            existingBar.parentNode.removeChild(existingBar);
        }

        // Auto-refresh preview after draft update
        // Chat history is saved in localStorage, so it will persist after refresh
        setTimeout(function() {
            location.reload();
        }, 800);

        var bar = document.createElement('div');
        bar.className = 'wxkn-publish-bar';
        bar.innerHTML =
            '<span>草稿已保存 - 正在刷新预览...</span>' +
            '<button class="wxkn-publish-btn">发布页面</button>';

        bar.querySelector('.wxkn-publish-btn').addEventListener('click', function() {
            confirmPublish();
        });

        bodyEl.appendChild(bar);
        scrollToBottom();
    }

    function confirmPublish() {
        showConfirmDialog(
            '确认发布',
            '确定要发布此页面吗？\n\n这将使当前草稿正式上线，对访客可见。',
            function() { doPublish(); }
        );
    }

    function doPublish() {
        var btn = document.querySelector('.wxkn-publish-btn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = '发布中...';
        }

        var params = new URLSearchParams();
        params.append('action', 'wxkn_preview_publish');
        params.append('_wpnonce', CONFIG.nonce);
        params.append('post_id', CONFIG.postId);

        fetch(CONFIG.ajaxUrl, { method: 'POST', body: params })
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.success) {
                    // Remove publish bar
                    var bar = document.querySelector('.wxkn-publish-bar');
                    if (bar) {
                        bar.parentNode.removeChild(bar);
                    }
                    appendMessage('system', '页面发布成功！');
                    // Reload to show published version
                    setTimeout(function () {
                        window.location.reload();
                    }, 800);
                } else {
                    if (btn) {
                        btn.disabled = false;
                        btn.textContent = '发布页面';
                    }
                    appendMessage('system', '发布失败: ' + ((res.data && res.data.message) || '未知错误'));
                }
            })
            .catch(function (err) {
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = '发布页面';
                }
                appendMessage('system', '发布错误: ' + err.message);
            });
    }

    function formatSize(bytes) {
        if (!bytes) return '0B';
        if (bytes < 1024) return bytes + 'B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB';
        return (bytes / (1024 * 1024)).toFixed(1) + 'MB';
    }

    /* ========================================================================
     * 12. DOM CREATION & EVENT BINDING
     * ======================================================================== */

    function createDOM() {
        // --- FAB with dropdown menu ---
        fab = document.createElement('div');
        fab.className = 'wxkn-chat-fab-wrap';

        fabBtn = document.createElement('button');
        fabBtn.className = 'wxkn-chat-fab';
        fabBtn.textContent = 'AI';
        fabBtn.addEventListener('click', toggleFabMenu);
        fab.appendChild(fabBtn);

        fabMenu = document.createElement('div');
        fabMenu.className = 'wxkn-fab-menu';
        fabMenu.innerHTML =
            '<button class="wxkn-fab-menu-item" data-fab-action="chat">AI 助手</button>' +
            '<button class="wxkn-fab-menu-item" data-fab-action="history"><i class="fa-solid fa-clock-rotate-left"></i> 历史</button>';
        fab.appendChild(fabMenu);

        // --- Widget ---
        widget = document.createElement('div');
        widget.className = 'wxkn-chat-widget';
        widget.style.display = 'none'; // Start hidden

        widget.innerHTML =
            '<div class="wxkn-chat-header">' +
            '  <span class="wxkn-chat-header-title">WXKN AI 助手</span>' +
            '  <div class="wxkn-chat-header-actions">' +
            '    <button class="wxkn-chat-header-btn" data-action="history" title="版本历史"><i class="fa-solid fa-clock-rotate-left"></i></button>' +
            '    <button class="wxkn-chat-header-btn" data-action="clear" title="清空对话"><i class="fa-solid fa-trash-can"></i></button>' +
            '    <button class="wxkn-chat-header-btn" data-action="minimize">&mdash;</button>' +
            '    <button class="wxkn-chat-header-btn" data-action="close">&times;</button>' +
            '  </div>' +
            '</div>' +
            '<div class="wxkn-chat-body"></div>' +
            '<div class="wxkn-chat-footer">' +
            '  <textarea class="wxkn-chat-input" rows="1" placeholder="输入消息..."></textarea>' +
            '  <button class="wxkn-chat-send">发送</button>' +
            '</div>';

        // Cache references to inner elements
        bodyEl = widget.querySelector('.wxkn-chat-body');
        inputEl = widget.querySelector('.wxkn-chat-input');
        sendBtn = widget.querySelector('.wxkn-chat-send');
        headerEl = widget.querySelector('.wxkn-chat-header');

        // --- Header button actions ---
        headerEl.querySelector('[data-action="minimize"]').addEventListener('click', minimizeWidget);
        headerEl.querySelector('[data-action="close"]').addEventListener('click', closeWidget);
        headerEl.querySelector('[data-action="history"]').addEventListener('click', function() { switchMode('history'); });
        headerEl.querySelector('[data-action="clear"]').addEventListener('click', clearConversation);

        // --- Drag ---
        headerEl.addEventListener('mousedown', onDragStart);
        document.addEventListener('mousemove', onDragMove);
        document.addEventListener('mouseup', onDragEnd);

        // --- Send button ---
        sendBtn.addEventListener('click', sendMessage);

        // --- Input Enter key (Shift+Enter for newline, Enter to send) ---
        inputEl.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // --- Textarea auto-resize ---
        inputEl.addEventListener('input', autoResizeTextarea);

        // --- Append to DOM ---
        document.body.appendChild(fab);
        document.body.appendChild(widget);

        // --- History Panel ---
        historyPanel = document.createElement('div');
        historyPanel.className = 'wxkn-history-panel';
        historyPanel.style.display = 'none';
        historyPanel.innerHTML =
            '<div class="wxkn-history-header">' +
            '  <button class="wxkn-history-back">&larr;</button>' +
            '  <span class="wxkn-history-header-title">版本历史</span>' +
            '</div>' +
            '<div class="wxkn-history-body">' +
            '  <select class="wxkn-history-target-select"></select>' +
            '  <ul class="wxkn-history-version-list"></ul>' +
            '  <div class="wxkn-history-preview-area" style="display:none">' +
            '    <textarea class="wxkn-history-preview-textarea" readonly></textarea>' +
            '  </div>' +
            '</div>' +
            '<div class="wxkn-history-footer">' +
            '  <button class="wxkn-history-restore-btn" disabled>恢复此版本</button>' +
            '</div>';
        document.body.appendChild(historyPanel);

        // History panel events
        historyPanel.querySelector('.wxkn-history-back').addEventListener('click', function() {
            switchMode('chat');
        });
        historyPanel.querySelector('.wxkn-history-restore-btn').addEventListener('click', confirmRestore);

        // FAB menu items
        fabMenu.querySelectorAll('.wxkn-fab-menu-item').forEach(function(item) {
            item.addEventListener('click', function() {
                var action = this.getAttribute('data-fab-action');
                switchMode(action);
            });
        });

        // Close menu on outside click
        document.addEventListener('click', function(e) {
            if (fabMenu && !fab.contains(e.target)) {
                fabMenu.style.display = 'none';
            }
        });
    }

    /* ========================================================================
     * 12b. INLINE EDIT - SELECTION & TOOLBAR
     * ======================================================================== */

    var inlineToolbar = null;
    var inlineProcessingEl = null;
    var selectionDebounceTimer = null;

    function initSelectionListener() {
        document.addEventListener('selectionchange', onSelectionChangeDebounced);
        document.addEventListener('mousedown', onDocumentMouseDown);
    }

    function onSelectionChangeDebounced() {
        if (selectionDebounceTimer) {
            clearTimeout(selectionDebounceTimer);
        }
        selectionDebounceTimer = setTimeout(onSelectionChange, 150);
    }

    function onDocumentMouseDown(e) {
        // Hide toolbar if clicking outside toolbar and outside preview dialog
        if (inlineToolbar && !inlineToolbar.contains(e.target)) {
            var previewOverlay = document.querySelector('.wxkn-inline-preview-overlay');
            if (!previewOverlay || !previewOverlay.contains(e.target)) {
                hideInlineToolbar();
            }
        }
    }

    function onSelectionChange() {
        var sel = window.getSelection();
        var text = sel.toString().trim();

        // Ignore selections inside widget or toolbar
        if (widget && widget.contains(sel.anchorNode)) {
            hideInlineToolbar();
            return;
        }
        if (inlineToolbar && inlineToolbar.contains(sel.anchorNode)) {
            return;
        }

        // Minimum length check
        if (text.length < 3) {
            hideInlineToolbar();
            return;
        }

        // Check if selection is valid range
        if (sel.rangeCount === 0) {
            hideInlineToolbar();
            return;
        }

        var range = sel.getRangeAt(0);
        var rect = range.getBoundingClientRect();

        // If selection has no dimensions (collapsed), hide toolbar
        if (rect.width === 0 && rect.height === 0) {
            hideInlineToolbar();
            return;
        }

        // Store selection info
        state.inlineEdit.originalText = text;
        state.inlineEdit.range = range.cloneRange();
        state.inlineEdit.rangeRect = rect;

        showInlineToolbar(rect);
    }

    function showInlineToolbar(rect) {
        if (!inlineToolbar) {
            createInlineToolbar();
        }

        // Calculate position: above selection, or below if too close to top
        var toolbarHeight = 40;
        var margin = 8;
        var top = rect.top - toolbarHeight - margin;
        var left = rect.left + (rect.width / 2);

        // If too close to top of viewport, show below
        if (top < 10) {
            top = rect.bottom + margin;
        }

        // Constrain to viewport
        var maxX = window.innerWidth - inlineToolbar.offsetWidth - 10;
        left = Math.max(10, Math.min(left - inlineToolbar.offsetWidth / 2, maxX));

        inlineToolbar.style.top = top + 'px';
        inlineToolbar.style.left = left + 'px';
        inlineToolbar.style.display = 'flex';
    }

    function hideInlineToolbar() {
        if (inlineToolbar) {
            inlineToolbar.style.display = 'none';
        }
    }

    function createInlineToolbar() {
        inlineToolbar = document.createElement('div');
        inlineToolbar.className = 'wxkn-inline-toolbar';
        inlineToolbar.style.display = 'none';

        var actions = [
            { action: 'edit', label: '编辑', icon: '' },
            { action: 'rewrite', label: '改写', icon: '' },
            { action: 'polish', label: '润色', icon: '' },
            { action: 'translate', label: '翻译', icon: '' },
            { action: 'summarize', label: '精简', icon: '' },
        ];

        actions.forEach(function(a) {
            var btn = document.createElement('button');
            btn.className = 'wxkn-inline-toolbar-btn';
            btn.setAttribute('data-action', a.action);
            btn.textContent = a.label;
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                onInlineActionClick(a.action);
            });
            inlineToolbar.appendChild(btn);
        });

        // Divider
        var divider = document.createElement('div');
        divider.className = 'wxkn-inline-toolbar-divider';
        inlineToolbar.appendChild(divider);

        // Custom button
        var customBtn = document.createElement('button');
        customBtn.className = 'wxkn-inline-toolbar-btn';
        customBtn.setAttribute('data-action', 'custom');
        customBtn.textContent = '自定义';
        customBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            showCustomPromptModal();
        });
        inlineToolbar.appendChild(customBtn);

        document.body.appendChild(inlineToolbar);
    }

    function onInlineActionClick(action) {
        if (state.inlineEdit.processing) return;

        state.inlineEdit.action = action;
        hideInlineToolbar();

        if (action === 'edit') {
            showInlineEditMode();
        } else if (action === 'custom') {
            showCustomPromptModal();
        } else {
            executeInlineEdit(action, state.inlineEdit.originalText, null);
        }
    }

    function showInlineEditMode() {
        var existing = document.querySelector('.wxkn-inline-edit-overlay');
        if (existing) existing.parentNode.removeChild(existing);

        var rect = state.inlineEdit.rangeRect;
        if (!rect) {
            rect = state.inlineEdit.range.getBoundingClientRect();
        }

        var overlay = document.createElement('div');
        overlay.className = 'wxkn-inline-edit-overlay';
        overlay.innerHTML =
            '<textarea class="wxkn-inline-edit-textarea"></textarea>' +
            '<div class="wxkn-inline-edit-footer">' +
            '  <button class="wxkn-inline-edit-btn-cancel">取消</button>' +
            '  <button class="wxkn-inline-edit-btn-save">保存</button>' +
            '</div>';

        var textarea = overlay.querySelector('.wxkn-inline-edit-textarea');
        var cancelBtn = overlay.querySelector('.wxkn-inline-edit-btn-cancel');
        var saveBtn = overlay.querySelector('.wxkn-inline-edit-btn-save');

        textarea.value = state.inlineEdit.originalText;
        textarea.style.width = Math.max(200, rect.width) + 'px';

        // Position near selection
        overlay.style.top = rect.top + 'px';
        overlay.style.left = rect.left + 'px';

        cancelBtn.addEventListener('click', function() {
            document.body.removeChild(overlay);
            state.inlineEdit.originalText = '';
            state.inlineEdit.range = null;
        });

        saveBtn.addEventListener('click', function() {
            var newText = textarea.value.trim();
            if (newText === state.inlineEdit.originalText) {
                // No change, just close
                document.body.removeChild(overlay);
                return;
            }
            if (!newText) {
                textarea.focus();
                return;
            }
            document.body.removeChild(overlay);
            state.inlineEdit.newText = newText;
            saveDraftAfterInlineEdit(state.inlineEdit.originalText, newText);
        });

        // Enter to save, Esc to cancel
        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                saveBtn.click();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelBtn.click();
            }
        });

        document.body.appendChild(overlay);
        textarea.focus();
        textarea.select();
    }

    /* ========================================================================
     * 12c. INLINE EDIT - CUSTOM PROMPT MODAL
     * ======================================================================== */

    function showCustomPromptModal() {
        var existing = document.querySelector('.wxkn-inline-custom-modal');
        if (existing) existing.parentNode.removeChild(existing);

        var overlay = document.createElement('div');
        overlay.className = 'wxkn-inline-custom-modal';
        overlay.innerHTML =
            '<div class="wxkn-inline-custom-dialog">' +
            '  <div class="wxkn-inline-custom-title">自定义指令</div>' +
            '  <textarea class="wxkn-inline-custom-textarea" placeholder="输入修改指令，如：改成更口语化、添加表情符号..."></textarea>' +
            '  <div class="wxkn-inline-custom-footer">' +
            '    <button class="wxkn-inline-custom-btn-cancel">取消</button>' +
            '    <button class="wxkn-inline-custom-btn-send">发送</button>' +
            '  </div>' +
            '</div>';

        var textarea = overlay.querySelector('.wxkn-inline-custom-textarea');
        var cancelBtn = overlay.querySelector('.wxkn-inline-custom-btn-cancel');
        var sendBtn = overlay.querySelector('.wxkn-inline-custom-btn-send');

        cancelBtn.addEventListener('click', function() {
            document.body.removeChild(overlay);
        });

        sendBtn.addEventListener('click', function() {
            var customPrompt = textarea.value.trim();
            if (!customPrompt) {
                textarea.focus();
                return;
            }
            document.body.removeChild(overlay);
            executeInlineEdit('custom', state.inlineEdit.originalText, customPrompt);
        });

        // Close on overlay click
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
            }
        });

        document.body.appendChild(overlay);
        textarea.focus();
    }

    /* ========================================================================
     * 12d. INLINE EDIT - AJAX & PREVIEW
     * ======================================================================== */

    async function executeInlineEdit(action, selectedText, customPrompt) {
        state.inlineEdit.processing = true;
        showInlineProcessing(action, state.inlineEdit.rangeRect);

        var params = new URLSearchParams();
        params.append('action', 'wxkn_preview_inline_edit');
        params.append('_wpnonce', CONFIG.nonce);
        params.append('post_id', CONFIG.postId);
        params.append('action_type', action);
        params.append('selected_text', selectedText);
        if (customPrompt) params.append('custom_prompt', customPrompt);

        try {
            var response = await fetch(CONFIG.ajaxUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: params.toString(),
            });
            var result = await response.json();

            hideInlineProcessing();

            if (!result.success) {
                appendMessage('system', '改写错误: ' + ((result.data && result.data.message) || '未知错误'));
                state.inlineEdit.processing = false;
                return;
            }

            state.inlineEdit.newText = result.data.new_text;
            showDiffPreview(state.inlineEdit.originalText, state.inlineEdit.newText, action);

        } catch (err) {
            hideInlineProcessing();
            appendMessage('system', '网络错误: ' + err.message);
        }

        state.inlineEdit.processing = false;
    }

    function showInlineProcessing(action, rect) {
        if (!inlineProcessingEl) {
            inlineProcessingEl = document.createElement('div');
            inlineProcessingEl.className = 'wxkn-inline-processing';
            inlineProcessingEl.innerHTML =
                '<div class="wxkn-inline-processing-spinner"></div>' +
                '<span>处理中...</span>';
            document.body.appendChild(inlineProcessingEl);
        }

        var actionLabels = {
            rewrite: '改写',
            polish: '润色',
            translate: '翻译',
            summarize: '精简',
            custom: '处理',
        };

        inlineProcessingEl.querySelector('span').textContent = (actionLabels[action] || '处理') + '中...';
        inlineProcessingEl.style.display = 'flex';

        // Position near original selection
        var top = rect.top - 50;
        if (top < 10) top = rect.bottom + 10;
        inlineProcessingEl.style.top = top + 'px';
        inlineProcessingEl.style.left = rect.left + 'px';
    }

    function hideInlineProcessing() {
        if (inlineProcessingEl) {
            inlineProcessingEl.style.display = 'none';
        }
    }

    function showDiffPreview(original, newText, action) {
        var existing = document.querySelector('.wxkn-inline-preview-overlay');
        if (existing) existing.parentNode.removeChild(existing);

        var actionLabels = {
            rewrite: '改写',
            polish: '润色',
            translate: '翻译',
            summarize: '精简',
            custom: '自定义',
        };

        var overlay = document.createElement('div');
        overlay.className = 'wxkn-inline-preview-overlay';
        overlay.innerHTML =
            '<div class="wxkn-inline-preview-dialog">' +
            '  <div class="wxkn-inline-preview-header">' + actionLabels[action] + '结果对比</div>' +
            '  <div class="wxkn-inline-preview-body">' +
            '    <div class="wxkn-inline-preview-pane">' +
            '      <div class="wxkn-inline-preview-pane-label">原文</div>' +
            '      <div class="wxkn-inline-preview-pane-content wxkn-inline-preview-pane-original"></div>' +
            '    </div>' +
            '    <div class="wxkn-inline-preview-pane">' +
            '      <div class="wxkn-inline-preview-pane-label">新文</div>' +
            '      <div class="wxkn-inline-preview-pane-content wxkn-inline-preview-pane-new"></div>' +
            '    </div>' +
            '  </div>' +
            '  <div class="wxkn-inline-preview-footer">' +
            '    <button class="wxkn-inline-preview-btn-reject">取消</button>' +
            '    <button class="wxkn-inline-preview-btn-accept">确认替换</button>' +
            '  </div>' +
            '</div>';

        overlay.querySelector('.wxkn-inline-preview-pane-original').textContent = original;
        overlay.querySelector('.wxkn-inline-preview-pane-new').textContent = newText;

        var acceptBtn = overlay.querySelector('.wxkn-inline-preview-btn-accept');
        var rejectBtn = overlay.querySelector('.wxkn-inline-preview-btn-reject');

        acceptBtn.addEventListener('click', function() {
            document.body.removeChild(overlay);
            onAcceptInlineEdit();
        });

        rejectBtn.addEventListener('click', function() {
            document.body.removeChild(overlay);
            onRejectInlineEdit();
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
                onRejectInlineEdit();
            }
        });

        document.body.appendChild(overlay);
    }

    function onAcceptInlineEdit() {
        // Send to backend for content replacement and draft save
        saveDraftAfterInlineEdit(state.inlineEdit.originalText, state.inlineEdit.newText);
    }

    function onRejectInlineEdit() {
        // Clear state
        state.inlineEdit.originalText = '';
        state.inlineEdit.newText = '';
        state.inlineEdit.range = null;
        state.inlineEdit.action = '';
    }

    async function saveDraftAfterInlineEdit(originalText, newText) {
        // Get page content from backend first
        var params = new URLSearchParams();
        params.append('action', 'wxkn_preview_inline_edit');
        params.append('_wpnonce', CONFIG.nonce);
        params.append('post_id', CONFIG.postId);
        params.append('action_type', 'get_content');
        params.append('selected_text', '');

        try {
            var response = await fetch(CONFIG.ajaxUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: params.toString(),
            });
            var result = await response.json();

            if (!result.success) {
                appendMessage('system', '获取页面内容失败');
                return;
            }

            var pageContent = result.data.content || '';

            // Replace in content
            var newContent = pageContent;
            var replaced = false;

            // Try direct match
            if (pageContent.indexOf(originalText) !== -1) {
                newContent = pageContent.replace(originalText, newText);
                replaced = true;
            }

            // Try with <br> variants
            if (!replaced) {
                var brVariants = ['<br>', '<br/>', '<br />'];
                for (var i = 0; i < brVariants.length; i++) {
                    var br = brVariants[i];
                    var originalWithBr = originalText.replace(/\n/g, br);
                    var newWithBr = newText.replace(/\n/g, br);
                    if (pageContent.indexOf(originalWithBr) !== -1) {
                        newContent = pageContent.replace(originalWithBr, newWithBr);
                        replaced = true;
                        break;
                    }
                }
            }

            // Try with paragraph tags
            if (!replaced) {
                var originalWithP = originalText.replace(/\n/g, '</p>\n<p>');
                var newWithP = newText.replace(/\n/g, '</p>\n<p>');
                if (pageContent.indexOf(originalWithP) !== -1) {
                    newContent = pageContent.replace(originalWithP, newWithP);
                    replaced = true;
                }
            }

            if (!replaced) {
                // Show AI replace option
                showAiReplaceOption(originalText, newText);
                return;
            }

            // Save new content
            var saveParams = new URLSearchParams();
            saveParams.append('action', 'wxkn_preview_inline_save');
            saveParams.append('_wpnonce', CONFIG.nonce);
            saveParams.append('post_id', CONFIG.postId);
            saveParams.append('content', newContent);

            var saveResponse = await fetch(CONFIG.ajaxUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: saveParams.toString(),
            });
            var saveResult = await saveResponse.json();

            if (saveResult.success) {
                appendMessage('system', '草稿已保存');
                showPublishBar();
            } else {
                appendMessage('system', '保存失败: ' + ((saveResult.data && saveResult.data.message) || '未知错误'));
            }
        } catch (err) {
            appendMessage('system', '网络错误: ' + err.message);
        }
    }

    function showAiReplaceOption(originalText, newText) {
        var existing = document.querySelector('.wxkn-ai-replace-modal');
        if (existing) existing.parentNode.removeChild(existing);

        var overlay = document.createElement('div');
        overlay.className = 'wxkn-confirm-overlay';
        overlay.innerHTML =
            '<div class="wxkn-confirm-dialog">' +
            '  <div class="wxkn-confirm-title">无法找到原文</div>' +
            '  <div class="wxkn-confirm-message">页面格式与选中文字不匹配，是否让AI智能查找并替换？<br><br>' +
            '    <strong>原文:</strong> ' + escapeHtml(originalText.substring(0, 50)) + (originalText.length > 50 ? '...' : '') + '<br>' +
            '    <strong>新文:</strong> ' + escapeHtml(newText.substring(0, 50)) + (newText.length > 50 ? '...' : '') +
            '  </div>' +
            '  <div class="wxkn-confirm-actions">' +
            '    <button class="wxkn-confirm-btn-cancel">取消</button>' +
            '    <button class="wxkn-ai-replace-btn">让AI帮我改</button>' +
            '  </div>' +
            '</div>';

        overlay.querySelector('.wxkn-confirm-btn-cancel').addEventListener('click', function() {
            document.body.removeChild(overlay);
        });

        overlay.querySelector('.wxkn-ai-replace-btn').addEventListener('click', function() {
            document.body.removeChild(overlay);
            executeAiReplace(originalText, newText);
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
            }
        });

        document.body.appendChild(overlay);
    }

    async function executeAiReplace(originalText, newText) {
        appendMessage('system', 'AI正在查找并替换...');

        var params = new URLSearchParams();
        params.append('action', 'wxkn_preview_inline_ai_replace');
        params.append('_wpnonce', CONFIG.nonce);
        params.append('post_id', CONFIG.postId);
        params.append('original_text', originalText);
        params.append('new_text', newText);

        try {
            var response = await fetch(CONFIG.ajaxUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: params.toString(),
            });
            var result = await response.json();

            if (result.success) {
                appendMessage('system', 'AI替换成功，草稿已保存');
                showPublishBar();
            } else {
                appendMessage('system', 'AI替换失败: ' + ((result.data && result.data.message) || '未知错误'));
            }
        } catch (err) {
            appendMessage('system', '网络错误: ' + err.message);
        }
    }

    /* ========================================================================
     * 13. INITIALIZATION
     * ======================================================================== */

    function init() {
        injectStyles();
        createDOM();

        // Restore position
        loadPosition();
        applyPosition();

        // Restore history
        loadHistory();
        renderMessages();

        // Check for autosave on load (show publish button if draft exists)
        checkAutosave();

        // Init inline edit selection listener
        initSelectionListener();

        // Check if this is a refresh after AI draft update (preview=true in URL)
        var urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('preview') === 'true') {
            expandWidget();
        } else {
            minimizeWidget();
        }
    }

    function checkAutosave() {
        var params = new URLSearchParams();
        params.append('action', 'wxkn_preview_check_autosave');
        params.append('_wpnonce', CONFIG.nonce);
        params.append('post_id', CONFIG.postId);

        fetch(CONFIG.ajaxUrl, { method: 'POST', body: params })
            .then(function (r) { return r.json(); })
            .then(function (res) {
                if (res.success && res.data && res.data.has_autosave) {
                    showPublishBarOnLoad();
                }
            })
            .catch(function (err) { console.error('[wxkn] check autosave failed:', err); });
    }

    function showPublishBarOnLoad() {
        // Remove existing publish bar first
        var existingBar = document.querySelector('.wxkn-publish-bar');
        if (existingBar) {
            existingBar.parentNode.removeChild(existingBar);
        }

        var bar = document.createElement('div');
        bar.className = 'wxkn-publish-bar';
        bar.innerHTML =
            '<span>有草稿待发布 - 点击发布按钮</span>' +
            '<button class="wxkn-publish-btn">发布页面</button>';

        bar.querySelector('.wxkn-publish-btn').addEventListener('click', function() {
            confirmPublish();
        });

        bodyEl.appendChild(bar);
        scrollToBottom();
    }

    // Wait for DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
