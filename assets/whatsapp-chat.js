(function () {
  'use strict';

  var WHATSAPP_BASE = 'https://wa.me/';

  function initWhatsAppChat() {
    var root = document.querySelector('[data-wa-chat]');
    if (!root) {
      return;
    }

    var toggle = root.querySelector('[data-wa-toggle]');
    var panel = root.querySelector('[data-wa-panel]');
    var closeButton = root.querySelector('[data-wa-close]');
    var form = root.querySelector('[data-wa-form]');
    var input = root.querySelector('[data-wa-input]');
    var number = (root.getAttribute('data-wa-number') || '').replace(/\D/g, '');

    if (!toggle || !panel) {
      return;
    }

    function isOpen() {
      return !panel.hidden;
    }

    function setOpen(open) {
      if (open) {
        panel.hidden = false;
        root.classList.add('is-open');
        toggle.setAttribute('aria-expanded', 'true');
        var finePointer = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;
        if (finePointer && input) {
          input.focus();
        } else {
          panel.focus();
        }
      } else {
        panel.hidden = true;
        root.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    }

    toggle.addEventListener('click', function (event) {
      event.preventDefault();
      setOpen(!isOpen());
    });

    if (closeButton) {
      closeButton.addEventListener('click', function () {
        setOpen(false);
        toggle.focus();
      });
    }

    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape' || !isOpen()) {
        return;
      }
      setOpen(false);
      toggle.focus();
    });

    document.addEventListener('click', function (event) {
      if (!isOpen() || root.contains(event.target)) {
        return;
      }
      setOpen(false);
    });

    if (input && form) {
      input.addEventListener('keydown', function (event) {
        if (event.key !== 'Enter' || event.shiftKey || event.isComposing) {
          return;
        }
        event.preventDefault();
        if (form.requestSubmit) {
          form.requestSubmit();
        } else {
          form.submit();
        }
      });
    }

    if (form) {
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        var message = input ? input.value.trim() : '';
        var url = WHATSAPP_BASE + number;
        if (message) {
          url += '?text=' + encodeURIComponent(message);
        }
        var link = document.createElement('a');
        link.href = url;
        link.target = '_blank';
        link.rel = 'noopener';
        document.body.appendChild(link);
        link.click();
        link.remove();
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWhatsAppChat);
  } else {
    initWhatsAppChat();
  }
})();
