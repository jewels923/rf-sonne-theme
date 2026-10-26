<?php
/**
 * 404 template for the SONNE theme.
 *
 * Uses the same chrome sequence as page.php: core header, branded header part,
 * a single main landmark, branded footer part and core footer.
 *
 * @package generatepress-child
 */

get_header();

get_template_part( 'template-parts/header' );
?>

<main id="main-content" class="sn-404">
	<style>
		.sn-404 {
			background: var(--sn-navy-deep);
			color: var(--sn-text);
		}
		.sn-404 *,
		.sn-404 *::before,
		.sn-404 *::after {
			box-sizing: border-box;
		}
		.sn-404 h1,
		.sn-404 h2,
		.sn-404 h3,
		.sn-404 p,
		.sn-404 ul,
		.sn-404 li {
			margin-top: 0;
		}
		.sn-404 a {
			text-underline-offset: 3px;
		}
		.sn-404 :focus-visible {
			outline: 3px solid var(--sn-cyan-dark);
			outline-offset: 3px;
		}
		.sn-404 .sn-404__hero :focus-visible,
		.sn-404 .sn-404__search-input:focus-visible {
			outline-color: var(--sn-accent-on-dark);
		}
		.sn-404 .sn-404__hero {
			padding-block: clamp(150px, 16vw, 210px) clamp(64px, 8vw, 100px);
		}
		.sn-404 .sn-404__hero::after {
			position: absolute;
			right: -8%;
			bottom: -30%;
			width: min(560px, 70vw);
			height: min(560px, 70vw);
			border-radius: 50%;
			background: radial-gradient(circle, rgba(11, 92, 213, .28) 0%, rgba(11, 92, 213, 0) 68%);
			content: '';
			pointer-events: none;
			z-index: 0;
		}
		.sn-404 .sn-404__grid {
			display: grid;
			grid-template-columns: minmax(0, 1.1fr) minmax(280px, .9fr);
			gap: clamp(32px, 6vw, 72px);
			align-items: center;
		}
		.sn-404 .sn-404__eyebrow {
			display: block;
			margin-bottom: 16px;
			color: var(--sn-accent-on-dark);
			font-family: var(--sn-font-mono);
			font-size: .75rem;
			font-weight: 700;
			letter-spacing: .09em;
			line-height: 1.5;
			text-transform: uppercase;
		}
		.sn-404 .sn-404__hero h1 {
			max-width: 16ch;
			margin-bottom: 22px;
			color: var(--sn-white);
			font-size: clamp(2.4rem, 5vw, 4.15rem);
			line-height: 1.06;
			letter-spacing: -.035em;
		}
		.sn-404 .sn-404__hero p {
			max-width: 62ch;
			margin-bottom: 16px;
			color: rgba(252, 254, 255, .82);
			font-size: 1.04rem;
			line-height: 1.7;
		}
		.sn-404 .sn-404__hero-note {
			max-width: 62ch;
			margin-bottom: 26px;
			padding: 14px 18px;
			border: 1px solid rgba(140, 196, 255, .35);
			border-radius: var(--sn-radius);
			background: rgba(252, 254, 255, .06);
			color: rgba(252, 254, 255, .8) !important;
			font-size: .88rem !important;
		}
		.sn-404 .sn-404__search {
			max-width: 560px;
			margin-bottom: 24px;
		}
		.sn-404 .sn-404__search-label {
			display: block;
			margin-bottom: 8px;
			color: rgba(252, 254, 255, .72);
			font-family: var(--sn-font-mono);
			font-size: .72rem;
			font-weight: 700;
			letter-spacing: .06em;
			text-transform: uppercase;
		}
		.sn-404 .sn-404__search-row {
			display: flex;
			border: 1px solid rgba(252, 254, 255, .3);
			background: rgba(252, 254, 255, .06);
		}
		.sn-404 .sn-404__search-row:focus-within {
			border-color: var(--sn-cyan);
		}
		.sn-404 .sn-404__search-input {
			flex: 1 1 auto;
			min-width: 0;
			min-height: 52px;
			padding: 12px 16px;
			border: 0;
			border-radius: 0;
			background: transparent;
			color: var(--sn-white);
			font-family: var(--sn-font-body);
			font-size: .95rem;
		}
		.sn-404 .sn-404__search-input::placeholder {
			color: rgba(252, 254, 255, .5);
		}
		.sn-404 .sn-404__search-button {
			flex: 0 0 auto;
			min-height: 52px;
			padding: 12px 24px;
			border: 0;
			border-radius: 0;
			background: var(--sn-accent);
			color: var(--sn-paper);
			font-family: var(--sn-font-body);
			font-size: .875rem;
			font-weight: 700;
			cursor: pointer;
		}
		.sn-404 .sn-404__search-button:hover {
			background: var(--sn-accent-dark);
		}
		.sn-404 .sn-404__actions {
			display: flex;
			flex-wrap: wrap;
			gap: 12px;
		}
		.sn-404 .sn-404__code {
			margin: 0;
			color: transparent;
			font-family: var(--sn-font-heading);
			font-size: clamp(120px, 18vw, 240px);
			font-weight: 800;
			line-height: .9;
			letter-spacing: -.06em;
			text-align: right;
			-webkit-text-stroke: 2px rgba(140, 196, 255, .45);
		}
		.sn-404 .sn-404__code-caption {
			margin: 18px 0 0;
			color: rgba(252, 254, 255, .62);
			font-family: var(--sn-font-mono);
			font-size: .72rem;
			line-height: 1.6;
			text-align: right;
		}
		.sn-404 .sn-404__destinations {
			background: var(--sn-white);
			padding-block: var(--sn-section-space);
		}
		.sn-404 .sn-404__destinations-intro {
			max-width: 800px;
			margin-bottom: 34px;
		}
		.sn-404 .sn-404__destinations-intro h2 {
			margin-bottom: 14px;
			color: var(--sn-navy);
			font-size: var(--sn-h2-size);
			line-height: var(--sn-h2-leading);
			letter-spacing: var(--sn-h2-tracking);
		}
		.sn-404 .sn-404__destinations-intro p {
			margin-bottom: 0;
			color: var(--sn-text-muted);
			line-height: 1.7;
		}
		.sn-404 .sn-404__links {
			display: grid;
			grid-template-columns: repeat(4, minmax(0, 1fr));
			gap: 14px;
			margin: 0;
			padding: 0;
			list-style: none;
		}
		.sn-404 .sn-404__link-card {
			display: flex;
			min-width: 0;
			min-height: 100%;
			flex-direction: column;
			gap: 6px;
			padding: 20px;
			border: var(--sn-border);
			background: var(--sn-white);
			color: var(--sn-text);
			text-decoration: none;
		}
		.sn-404 .sn-404__link-card:hover,
		.sn-404 .sn-404__link-card:focus-visible {
			border-color: var(--sn-cyan-dark);
			box-shadow: var(--sn-shadow);
		}
		.sn-404 .sn-404__link-label {
			display: flex;
			gap: 8px;
			align-items: center;
			color: var(--sn-navy);
			font-family: var(--sn-font-heading);
			font-size: 1rem;
			font-weight: 700;
			line-height: 1.35;
		}
		.sn-404 .sn-404__link-label::after {
			margin-left: auto;
			color: var(--sn-cyan-dark);
			font-family: var(--sn-font-mono);
			content: '→';
		}
		.sn-404 .sn-404__link-desc {
			color: var(--sn-text-muted);
			font-size: .82rem;
			line-height: 1.55;
		}
		.sn-404 .sn-404__contact {
			margin: 28px 0 0;
			color: var(--sn-text-muted);
			font-size: .9rem;
			line-height: 1.7;
		}
		.sn-404 .sn-404__contact a {
			color: var(--sn-cyan-dark);
			font-weight: 700;
		}
		@media (max-width: 1024px) {
			.sn-404 .sn-404__grid {
				grid-template-columns: 1fr;
			}
			.sn-404 .sn-404__code {
				text-align: left;
			}
			.sn-404 .sn-404__code-caption {
				text-align: left;
			}
			.sn-404 .sn-404__links {
				grid-template-columns: repeat(2, minmax(0, 1fr));
			}
		}
		@media (max-width: 600px) {
			.sn-404 .sn-404__links {
				grid-template-columns: 1fr;
			}
			.sn-404 .sn-404__search-row {
				flex-direction: column;
			}
			.sn-404 .sn-404__search-button {
				width: 100%;
			}
			.sn-404 .sn-404__actions .sn-btn {
				width: 100%;
			}
		}
	</style>

	<section class="sn-hero sn-404__hero" aria-labelledby="sn-404-title">
		<div class="sn-container sn-404__grid">
			<div>
				<span class="sn-404__eyebrow">404 · Address not found</span>
				<h1 id="sn-404-title">Page Not Found</h1>
				<p>The page you requested is not available at this address. It may have moved during the site rebuild, or the link may contain a typo.</p>
				<p class="sn-404__hero-note">Search the site below, or continue from one of the main sections.</p>
				<form class="sn-404__search" role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>">
					<label class="sn-404__search-label" for="sn-404-search">Search the SONNE website</label>
					<div class="sn-404__search-row">
						<input class="sn-404__search-input" id="sn-404-search" type="search" name="s" value="<?php echo esc_attr( get_search_query() ); ?>" placeholder="Product, application or document">
						<button class="sn-404__search-button" type="submit">Search</button>
					</div>
				</form>
				<div class="sn-404__actions">
					<a class="sn-btn sn-btn--primary" href="<?php echo esc_url( home_url( '/' ) ); ?>">Back to Home</a>
					<a class="sn-btn sn-btn--secondary" href="<?php echo esc_url( home_url( '/request-a-quote/' ) ); ?>">Request a Quote</a>
				</div>
			</div>
			<div>
				<p class="sn-404__code" aria-hidden="true">404</p>
				<p class="sn-404__code-caption">RF filters · Waveguide · Combiners<br>Base-station RF · Precision enclosures</p>
			</div>
		</div>
	</section>

	<section class="sn-404__destinations" aria-labelledby="sn-404-destinations-title">
		<div class="sn-container">
			<header class="sn-404__destinations-intro">
				<h2 id="sn-404-destinations-title">Popular Destinations</h2>
				<p>Open a section directly, or start with the product line closest to your requirement.</p>
			</header>
			<ul class="sn-404__links">
				<li>
					<a class="sn-404__link-card" href="<?php echo esc_url( home_url( '/' ) ); ?>">
						<span class="sn-404__link-label">Home</span>
						<span class="sn-404__link-desc">Product matrix, engineering evidence and project routes.</span>
					</a>
				</li>
				<li>
					<a class="sn-404__link-card" href="<?php echo esc_url( home_url( '/products/' ) ); ?>">
						<span class="sn-404__link-label">Products</span>
						<span class="sn-404__link-desc">Filters, waveguide, combiners, base-station RF and enclosures.</span>
					</a>
				</li>
				<li>
					<a class="sn-404__link-card" href="<?php echo esc_url( home_url( '/solutions/' ) ); ?>">
						<span class="sn-404__link-label">Solutions</span>
						<span class="sn-404__link-desc">Component sets by application, from 5G sites to earth stations.</span>
					</a>
				</li>
				<li>
					<a class="sn-404__link-card" href="<?php echo esc_url( home_url( '/engineering/' ) ); ?>">
						<span class="sn-404__link-label">Engineering</span>
						<span class="sn-404__link-desc">Design, NPI, testing and precision manufacturing workstreams.</span>
					</a>
				</li>
				<li>
					<a class="sn-404__link-card" href="<?php echo esc_url( home_url( '/resources/' ) ); ?>">
						<span class="sn-404__link-label">Resources</span>
						<span class="sn-404__link-desc">Insights, RFQ guide, FAQ and engineering documents.</span>
					</a>
				</li>
				<li>
					<a class="sn-404__link-card" href="<?php echo esc_url( home_url( '/about/' ) ); ?>">
						<span class="sn-404__link-label">About</span>
						<span class="sn-404__link-desc">Company background, capability facts and factory evidence.</span>
					</a>
				</li>
				<li>
					<a class="sn-404__link-card" href="<?php echo esc_url( home_url( '/contact/' ) ); ?>">
						<span class="sn-404__link-label">Contact</span>
						<span class="sn-404__link-desc">Send a technical question to the SONNE team.</span>
					</a>
				</li>
				<li>
					<a class="sn-404__link-card" href="<?php echo esc_url( home_url( '/request-a-quote/' ) ); ?>">
						<span class="sn-404__link-label">Request a Quote</span>
						<span class="sn-404__link-desc">Submit a band plan, specification or drawing for review.</span>
					</a>
				</li>
			</ul>
			<p class="sn-404__contact">Still stuck? Email <a href="mailto:info@zhide-tec.com">info@zhide-tec.com</a> and include the address you tried to open.</p>
		</div>
	</section>
</main>

<?php
get_template_part( 'template-parts/footer' );

get_footer();
