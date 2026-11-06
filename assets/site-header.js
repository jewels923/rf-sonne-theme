(function () {
    function initSiteHeader() {
        var shell = document.querySelector('.site-header-shell');
        if (!shell) {
            return;
        }

        var body = document.body;

        // Global: every page gets the transparent-over-hero → solid-on-scroll header treatment.
        // Try every known page-hero class; fall back to a fixed threshold if none is found.
        var homeHero = document.querySelector('.sn-hero, .refit-hero, .hero-shell, .home-hero, .jl-hero, .pd-hero, .cs-hero, .jc-hero, .au-hero, .su-hero, .kl-hero');

        var openButton = shell.querySelector('.site-menu-toggle');
        var drawer = shell.querySelector('.site-mobile-nav');
        var closeButton = shell.querySelector('.site-mobile-nav__close');

        function setDrawerState(isOpen) {
            if (!drawer || !openButton) {
                return;
            }

            drawer.hidden = !isOpen;
            openButton.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            document.body.classList.toggle('site-nav-open', isOpen);
        }

        if (openButton) {
            openButton.addEventListener('click', function () {
                var expanded = openButton.getAttribute('aria-expanded') === 'true';
                setDrawerState(!expanded);
            });
        }

        if (closeButton) {
            closeButton.addEventListener('click', function () {
                setDrawerState(false);
            });
        }

        shell.querySelectorAll('.site-mobile-nav__toggle').forEach(function (toggleButton) {
            toggleButton.addEventListener('click', function () {
                var item = toggleButton.closest('.site-mobile-nav__item');
                var submenu = item ? item.querySelector('.site-mobile-nav__submenu') : null;
                var expanded = toggleButton.getAttribute('aria-expanded') === 'true';

                toggleButton.setAttribute('aria-expanded', expanded ? 'false' : 'true');

                if (submenu) {
                    submenu.hidden = expanded;
                }
            });
        });

        var langSwitchers = shell.querySelectorAll('[data-site-lang]');

        function closeLangSwitchers(except) {
            langSwitchers.forEach(function (item) {
                if (item !== except) {
                    item.open = false;
                }
            });
        }

        langSwitchers.forEach(function (item) {
            item.addEventListener('toggle', function () {
                if (item.open) {
                    closeLangSwitchers(item);
                }
            });
            item.addEventListener('click', function (event) {
                if (event.target.closest('a')) {
                    item.open = false;
                }
            });
            item.addEventListener('focusout', function (event) {
                if (event.relatedTarget && item.contains(event.relatedTarget)) {
                    return;
                }
                item.open = false;
            });
        });

        document.addEventListener('click', function (event) {
            if (!event.target.closest('[data-site-lang]')) {
                closeLangSwitchers();
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key !== 'Escape') {
                return;
            }
            langSwitchers.forEach(function (item) {
                if (!item.open) {
                    return;
                }
                item.open = false;
                var toggle = item.querySelector('summary');
                if (toggle) {
                    toggle.focus();
                }
            });
        });

        var previewImg = document.getElementById('productPreviewImg');
        var megaMenu = document.querySelector('.site-nav__dropdown--mega');
        var defaultImgSrc = previewImg ? previewImg.getAttribute('src') : '';
        var defaultImgAlt = previewImg ? previewImg.getAttribute('alt') : 'Preview';
        var hoverItems = document.querySelectorAll('.hover-trigger');

        if (hoverItems.length > 0 && previewImg) {
            hoverItems.forEach(function (item) {
                item.addEventListener('mouseenter', function () {
                    var newSrc = this.getAttribute('data-img');
                    var newAlt = this.getAttribute('data-alt');

                    if (!newSrc) {
                        return;
                    }

                    previewImg.style.opacity = '0';

                    window.setTimeout(function () {
                        previewImg.src = newSrc;
                        previewImg.alt = newAlt || defaultImgAlt;
                        previewImg.style.opacity = '1';
                    }, 100);
                });
            });
        }

        if (megaMenu && previewImg) {
            megaMenu.addEventListener('mouseleave', function () {
                previewImg.style.opacity = '0';

                window.setTimeout(function () {
                    previewImg.src = defaultImgSrc;
                    previewImg.alt = defaultImgAlt;
                    previewImg.style.opacity = '1';
                }, 100);
            });
        }

        var ticking = false;

        function syncHomeHeaderState() {
            var threshold = homeHero
                ? Math.max(24, Math.min(homeHero.offsetHeight * 0.08, 120))
                : 80;
            var isScrolled = window.scrollY > threshold;
            body.classList.toggle('home-header-scrolled', isScrolled);
            var logo = shell.querySelector('.site-branding__logo');
            if (logo && logo.dataset.baseHeight) {
                var h = isScrolled ? (logo.dataset.scrollHeight || '35px') : logo.dataset.baseHeight;
                logo.style.maxHeight = h;
                logo.style.height = h;
            }
            ticking = false;
        }

        function requestHeaderSync() {
            if (ticking) {
                return;
            }

            ticking = true;
            window.requestAnimationFrame(syncHomeHeaderState);
        }

        syncHomeHeaderState();
        window.addEventListener('scroll', requestHeaderSync, { passive: true });
        window.addEventListener('resize', requestHeaderSync);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            initSiteHeader();
        });
    } else {
        initSiteHeader();
    }
}());
