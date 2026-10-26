/**
 * ALL-5-UI Global JavaScript
 * 
 * Includes:
 * 1. Lenis Smooth Scrolling (Awwwards standard)
 * 2. GSAP ScrollTrigger Integration
 * 3. Text Reveal Animations (.reveal-text)
 * 4. Image Parallax Effects (.parallax-inner)
 */

document.addEventListener("DOMContentLoaded", () => {
    // Make sure GSAP and Lenis are available
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined' || typeof Lenis === 'undefined') {
        console.warn("ALL-5-UI: GSAP, ScrollTrigger, or Lenis is missing.");
        return;
    }

    // Register ScrollTrigger
    gsap.registerPlugin(ScrollTrigger);

    // =========================================================================
    // 1. Initialize Lenis Smooth Scroll
    // =========================================================================
    const lenis = new Lenis({
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // Custom physics-based easing
        direction: 'vertical',
        gestureDirection: 'vertical',
        smooth: true,
        smoothTouch: false, // Don't interfere with native touch scrolling too much
        touchMultiplier: 2,
    });

    // Sync Lenis with GSAP ScrollTrigger
    lenis.on('scroll', ScrollTrigger.update);

    gsap.ticker.add((time) => {
        lenis.raf(time * 1000);
    });
    gsap.ticker.lagSmoothing(0);

    // =========================================================================
    // 2. Text Reveal Animations (.reveal-text)
    // =========================================================================
    // Select all elements that should reveal
    const revealElements = document.querySelectorAll('.reveal-text');
    
    revealElements.forEach((el) => {
        // Wrap contents in .reveal-inner for the CSS clip-path animation to work
        const innerHTML = el.innerHTML;
        el.innerHTML = '';
        const wrapper = document.createElement('span');
        wrapper.className = 'reveal-inner';
        wrapper.innerHTML = innerHTML;
        el.appendChild(wrapper);

        gsap.to(el, {
            scrollTrigger: {
                trigger: el,
                start: "top 90%", // Trigger when top of element hits 90% of viewport
                toggleClass: "is-visible",
                once: true // Only play once
            }
        });
    });

    // =========================================================================
    // 3. Image Parallax (.parallax-wrap & .parallax-inner)
    // =========================================================================
    const parallaxWraps = document.querySelectorAll('.parallax-wrap');
    
    parallaxWraps.forEach((wrap) => {
        const inner = wrap.querySelector('.parallax-inner');
        if (!inner) return;

        // The image is 120% height and top: -10%. We move it from yPercent: -10 to yPercent: 10
        gsap.fromTo(inner, 
            { yPercent: -10 },
            {
                yPercent: 10,
                ease: "none",
                scrollTrigger: {
                    trigger: wrap,
                    start: "top bottom", // when top of wrap hits bottom of viewport
                    end: "bottom top",   // when bottom of wrap hits top of viewport
                    scrub: true          // link animation to scrollbar
                }
            }
        );
    });

    // =========================================================================
    // 4. Subtle Entry Animation for Glass Panels
    // =========================================================================
    const glassPanels = document.querySelectorAll('.glass-panel');
    glassPanels.forEach((panel, index) => {
        gsap.from(panel, {
            scrollTrigger: {
                trigger: panel,
                start: "top 95%",
                once: true
            },
            y: 40,
            opacity: 0,
            duration: 1,
            ease: "power3.out",
            clearProps: "all" // Remove inline styles after animation so hover states work
        });
    });

    // =========================================================================
    // 5. Button Magnetic/Hover Effect (Optional Creative Touch)
    // =========================================================================
    const magneticButtons = document.querySelectorAll('.btn-primary, .btn-secondary, .btn-outline, .btn-dark, .link-card');
    
    // We can add a subtle magnetic effect for desktop only
    if (window.matchMedia("(min-width: 1024px)").matches) {
        magneticButtons.forEach((btn) => {
            btn.addEventListener('mousemove', (e) => {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                
                gsap.to(btn, {
                    x: x * 0.15,
                    y: y * 0.15,
                    duration: 0.4,
                    ease: "power2.out"
                });
            });

            btn.addEventListener('mouseleave', () => {
                gsap.to(btn, {
                    x: 0,
                    y: 0,
                    duration: 0.7,
                    ease: "elastic.out(1, 0.3)"
                });
            });
        });
    }
});

// =========================================================================
// Global .reveal fallback (2026-07-19)
// Some refit pages were published without the inline reveal-on-scroll
// script, leaving .reveal elements stuck at opacity: 0 (blank hero).
// This standalone observer adds .in to any .reveal element site-wide.
// It has no GSAP/Lenis dependency and runs even if the block above bails.
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    const revealEls = document.querySelectorAll('.reveal:not(.in), .rv:not(.visible)');
    if (!revealEls.length) return;
    if (!('IntersectionObserver' in window)) {
        revealEls.forEach((el) => { el.classList.add('in'); el.classList.add('visible'); });
        return;
    }
    const revealIO = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in');
                entry.target.classList.add('visible');
                revealIO.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
    revealEls.forEach((el) => revealIO.observe(el));
});

// =========================================================================
// Lazy-image force-load (2026-07-20, broadened 2026-07-27)
// Lenis smooth scrolling uses CSS transforms on the scroll container,
// which breaks native loading="lazy": the browser's internal observer
// reads the real (un-transformed) position, so images that are visually
// in the viewport still appear "below the fold" to the lazy-load logic.
// Fix: our own IntersectionObserver (which respects visual position)
// watches EVERY lazy image directly and flips it to loading="eager"
// 300px before it enters the viewport. Observing images directly (not
// their parent sections) makes this work regardless of section class
// (.reveal / .rv / .pd-reveal / .section).
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    if (!('IntersectionObserver' in window)) return;
    const lazyImgs = document.querySelectorAll('img[loading="lazy"]');
    if (!lazyImgs.length) return;
    const imgIO = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.loading = 'eager';
                // Force re-fetch: some browsers won't start the deferred
                // fetch just from flipping loading=eager, so reset src.
                if (img.src && img.naturalWidth === 0) {
                    const s = img.src;
                    img.src = '';
                    img.src = s;
                }
                imgIO.unobserve(img);
            }
        });
    }, { threshold: 0.01, rootMargin: '300px 0px' });
    lazyImgs.forEach((img) => imgIO.observe(img));
});

// =========================================================================
// 6. Awwwards-Level Motion System (2026-07-20)
// Stagger reveals, counter animations, cinematic hero entrance,
// image scale parallax, and section heading clip-reveals.
// Respects prefers-reduced-motion. No scroll event listeners used.
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    // Guard: require GSAP + ScrollTrigger
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;
    gsap.registerPlugin(ScrollTrigger);

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // --- Reduced-motion fallback: make everything visible immediately ---
    if (prefersReducedMotion) {
        document.querySelectorAll('.rv, .rv-child').forEach((el) => {
            el.style.opacity = '1';
            el.style.transform = 'none';
        });
        document.querySelectorAll('.stats-band__value, [data-count]').forEach((el) => {
            // Leave text as-is (already shows final number in HTML)
        });
        document.querySelectorAll('.section-heading h2').forEach((el) => {
            el.style.clipPath = 'none';
            el.style.transform = 'none';
        });
        return; // Skip all animation setup
    }

    // Use gsap.context for scoped cleanup
    const ctx = gsap.context(() => {

        // =================================================================
        // 6a. REVEAL SYSTEM (.rv sections)
        // Section visibility is handled by the global IntersectionObserver
        // above (adds .visible, CSS transitions opacity/transform). We do NOT
        // hide children with gsap.set here - that previously left pages blank
        // because the .rv section itself never received .visible.
        // =================================================================

        // =================================================================
        // 6b. COUNTER ANIMATION (.stats-band__value / [data-count])
        // Animates number from 0 to target, preserving suffixes.
        // =================================================================
        const counterEls = document.querySelectorAll('.stats-band__value, [data-count]');
        counterEls.forEach((el) => {
            const rawText = el.textContent.trim();
            // Extract leading number (int or decimal) and trailing suffix
            const match = rawText.match(/^([\d,.]+)(.*)/);
            if (!match) return;

            const numStr = match[1].replace(/,/g, '');
            const targetNum = parseFloat(numStr);
            if (isNaN(targetNum)) return;

            const suffix = match[2] || '';
            const hasComma = match[1].includes(',');
            const decimals = (numStr.split('.')[1] || '').length;

            const counter = { val: 0 };

            gsap.to(counter, {
                val: targetNum,
                duration: 1.8,
                ease: "power2.out",
                snap: { val: decimals === 0 ? 1 : Math.pow(10, -decimals) },
                scrollTrigger: {
                    trigger: el,
                    start: "top 88%",
                    once: true
                },
                onUpdate: () => {
                    let display = decimals > 0
                        ? counter.val.toFixed(decimals)
                        : Math.round(counter.val).toString();
                    if (hasComma) {
                        display = Number(display).toLocaleString('en-US');
                    }
                    el.textContent = display + suffix;
                }
            });
        });

        // =================================================================
        // 6c. HERO ENTRANCE (.jl-hero-inner)
        // Cinematic load-in: eyebrow → h1 → sub → buttons → trust badges.
        // =================================================================
        const heroInner = document.querySelector('.jl-hero-inner');
        if (heroInner) {
            // Build ordered list of hero children for staggered entrance
            const heroTargets = [];
            const eyebrow = heroInner.querySelector('.hero-eyebrow, .jl-hero-eyebrow, [class*="eyebrow"]');
            const h1 = heroInner.querySelector('h1');
            const sub = heroInner.querySelector('.hero-sub, .jl-hero-sub, [class*="sub"], p');
            const buttons = heroInner.querySelector('.hero-buttons, .jl-hero-buttons, [class*="btn"], [class*="cta"]');
            const trust = heroInner.querySelector('.hero-trust, .jl-hero-trust, [class*="trust"], [class*="badge"]');

            if (eyebrow) heroTargets.push(eyebrow);
            if (h1) heroTargets.push(h1);
            if (sub) heroTargets.push(sub);
            if (buttons) heroTargets.push(buttons);
            if (trust) heroTargets.push(trust);

            // Fallback: if no specific selectors matched, use direct children
            const finalTargets = heroTargets.length ? heroTargets : Array.from(heroInner.children);

            gsap.set(finalTargets, { opacity: 0, y: (i) => [20, 30, 25, 20, 15][i] || 20 });

            gsap.to(finalTargets, {
                opacity: 1,
                y: 0,
                duration: 1,
                ease: "power3.out",
                stagger: 0.12,
                delay: 0.3
            });
        }

        // =================================================================
        // 6d. IMAGE PARALLAX UPGRADE (.prod-item__media img)
        // Subtle scale from 1.08 → 1.0 on scroll (scrub-linked).
        // =================================================================
        const prodImages = document.querySelectorAll('.prod-item__media img');
        prodImages.forEach((img) => {
            gsap.fromTo(img,
                { scale: 1.08 },
                {
                    scale: 1.0,
                    ease: "none",
                    scrollTrigger: {
                        trigger: img.closest('.prod-item__media') || img.parentElement,
                        start: "top bottom",
                        end: "bottom top",
                        scrub: true
                    }
                }
            );
        });

        // =================================================================
        // 6e. SECTION HEADING CLIP-REVEAL (.section-heading h2)
        // Clips from below with upward motion.
        // =================================================================
        const headingEls = document.querySelectorAll('.section-heading h2');
        headingEls.forEach((heading) => {
            gsap.set(heading, {
                clipPath: "inset(100% 0% 0% 0%)",
                y: 30
            });

            gsap.to(heading, {
                clipPath: "inset(0% 0% 0% 0%)",
                y: 0,
                duration: 1,
                ease: "power3.out",
                scrollTrigger: {
                    trigger: heading,
                    start: "top 88%",
                    once: true
                }
            });
        });

    }); // end gsap.context

    // Cleanup on page hide (SPA navigation, bfcache, etc.)
    window.addEventListener('pagehide', () => {
        ctx.revert();
    });
});