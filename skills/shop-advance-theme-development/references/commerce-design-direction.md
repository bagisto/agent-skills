# Commerce design direction

## Contents

- [Use design intelligence safely](#use-design-intelligence-safely)
- [Synthesize a defensible direction](#synthesize-a-defensible-direction)
- [Use a shared commerce vocabulary](#use-a-shared-commerce-vocabulary)
- [Set the design dials](#set-the-design-dials)
- [Define semantic tokens](#define-semantic-tokens)
- [Compose the complete storefront](#compose-the-complete-storefront)
- [Map visual sections to merchant data](#map-visual-sections-to-merchant-data)
- [Generate Bagisto UI/UX direction](#generate-bagisto-uiux-direction)
- [Filter generated recommendations](#filter-generated-recommendations)
- [Review before implementation](#review-before-implementation)

Read this reference for a new theme, a substantial redesign, a design-system request, or a request described as modern, premium, luxury, world-class, polished, or conversion-focused. Use it with `design-quality.md`; this file supplies decision vocabulary while that file supplies quality gates.

## Use design intelligence safely

Make design decisions in this precedence order:

1. Supplied brand standards, approved assets, and customer research.
2. Catalog character, price position, customer tasks, and available content.
3. Installed Bagisto commerce, extension, channel, locale, and runtime contracts.
4. Accessibility, performance, licensing, and browser requirements.
5. Curated design-system or recommendation output.
6. General style trends.

Never let a style label choose the architecture. A recommendation is useful only when it fits the merchandise, makes the next commerce action clearer, works with real content extremes, and can be implemented without weakening Bagisto behavior.

Do not treat “modern” as a visual specification. Resolve it into explicit choices for hierarchy, composition, density, type, color, imagery, surface, iconography, motion, and interaction states.

## Synthesize a defensible direction

Before selecting colors or components, write:

- one sentence connecting the brand promise, merchandise, and customer action;
- one primary archetype and at most one supporting influence;
- three to five visual principles that can be tested in a page review;
- explicit anti-goals that rule out generic or inappropriate patterns;
- the primary conversion journey and the content needed to support it;
- the intended balance between merchant storytelling and product discovery.

Use one dominant concept across the storefront. Allow page-specific composition, but do not give home, catalog, product, cart, and checkout unrelated visual systems.

## Use a shared commerce vocabulary

### Style archetypes

| Archetype | Customer impression | Appropriate use | Common failure |
|---|---|---|---|
| Editorial commerce | Curated, expressive, story-led | Fashion, fragrance, interiors, craft, premium launches | Hiding products behind oversized campaigns |
| Boutique luxury | Restrained, intimate, high-consideration | Premium catalogs with strong imagery and service | Low contrast, excessive whitespace, weak CTAs |
| Product-first retail | Clear, comparable, efficient | Broad catalogs and repeat-purchase goods | Generic grids with no brand character |
| Collection-led retail | Discoverable groups and coordinated ranges | Beauty, apparel, home, seasonal catalogs | Collections replacing useful search and filters |
| Marketplace utility | Dense, predictable, confidence-focused | Large mixed catalogs and price comparison | Visual noise and competing primary actions |
| Ingredient or evidence-led | Credible, explanatory, transparent | Skincare, wellness, technical or sustainable goods | Turning every page into dense documentation |
| Heritage craft | Tactile, storied, provenance-focused | Artisan, legacy, handmade, regional products | Decorative nostalgia that reduces usability |
| Immersive campaign | Cinematic, launch-focused, emotional | Limited collections and high-quality campaign assets | Heavy media, weak accessibility, slow LCP |

Choose an archetype because it supports the catalog and journey—not because its name sounds premium.

### Composition vocabulary

- **Symmetrical:** stable and formal; useful for trust and high-consideration products.
- **Asymmetrical:** energetic and editorial; require a clear reading order at every breakpoint.
- **Modular:** reusable section rhythm; useful for merchant-managed home content.
- **Full-bleed:** immersive media touching viewport edges; reserve dimensions and protect text contrast.
- **Split composition:** pair image and copy or product and evidence; define mobile stacking order.
- **Layered:** controlled overlap or depth; preserve focus, hit targets, and content legibility.
- **Product rail:** horizontal merchandising; provide keyboard controls and a non-carousel fallback.
- **Dense comparison:** compact cards or rows; preserve readable price, state, and touch targets.

### Visual-system vocabulary

- **Type voice:** editorial serif, humanist sans, geometric sans, technical grotesk, expressive display.
- **Surface language:** flat, bordered, softly elevated, tactile, translucent-with-purpose.
- **Shape language:** sharp, softly rounded, organic, restrained-pill. Avoid making every element a pill.
- **Image language:** studio, lifestyle, macro detail, ingredient, process, editorial, user-generated.
- **Icon language:** outline or filled, one family, consistent stroke, optical size, and state treatment.
- **Hierarchy:** display, heading, body, label, price, metadata, helper, status.
- **Merchandising hierarchy:** campaign-led, collection-led, product-led, search-led, or service-led.

## Set the design dials

Use integer values from 1 through 10. Explain each value in the brief; the number alone is insufficient.

| Dial | 1–3 | 4–7 | 8–10 | Commerce constraint |
|---|---|---|---|---|
| `variance` | Restrained, regular, highly predictable | Balanced hierarchy with selected asymmetric moments | Bold scale, rhythm, or composition changes | Product information and actions remain predictable |
| `motion` | State feedback and essential transitions only | Controlled reveals and spatial transitions | Expressive choreography on selected campaign surfaces | Never delay input, cart, options, checkout, or reduced-motion users |
| `density` | Spacious, low item count, large media | Balanced retail density | Compact catalog or comparison density | Maintain text size, tap targets, error clarity, and content reflow |

High values do not mean higher quality. Checkout normally needs lower variance and motion than campaign pages. Catalog density may be higher than product-detail density. Record page-specific exceptions rather than silently changing the system.

## Define semantic tokens

Define roles before assigning literal values:

- color: canvas, surface, elevated, text, muted, border, brand, accent, focus, success, warning, danger, price, sale, stock;
- typography: display, page title, section title, product title, body, label, price, metadata, helper;
- spacing: component, cluster, section, container gutter, content measure;
- shape: control, card, media, modal, badge;
- elevation: base, raised, overlay, modal;
- motion: fast, standard, deliberate, enter easing, exit easing, distance;
- layering: content, sticky, dropdown, drawer, modal, toast.

Map semantic roles onto the installed Tailwind contract. Preserve compatibility tokens and content globs required by inherited Shop views. Prefer CSS custom properties or a centralized Tailwind extension over raw values repeated in Blade.

Verify every foreground/background pair used by normal text, large text, controls, focus, errors, and non-text state indicators. Design hover, focus-visible, active, selected, loading, disabled, empty, error, and success states with the base component—not after the happy path.

## Compose the complete storefront

Give each surface a clear job:

| Surface | Primary design job | Preserve visibly |
|---|---|---|
| Header and navigation | Orientation and fast discovery | Search, category access, locale/currency, account, mini-cart |
| Home | Establish promise and route customers into merchandise | Merchant-managed blocks, useful server fallback, clear next action |
| Category and search | Help customers narrow and compare | Query/filter state, sort, view mode, pagination, empty state |
| Product card | Enable rapid recognition and comparison | Image, name, authoritative price, rating/state, actions and variants when supported |
| Product detail | Reduce decision uncertainty | Gallery, type-specific options, stock, price/tax, reviews, trust, related products |
| Cart | Confirm choices and expose corrections | Options, quantities, totals, coupon, estimates, errors and removal |
| Checkout | Build confidence through an ordered state machine | Address, shipping, payment, summary, validation and duplicate-submit prevention |
| Account and extensions | Make post-purchase tasks predictable | Installed navigation, permissions, statuses, history and extension output |
| CMS and system states | Keep the brand coherent outside shopping paths | Metadata, readable content, recovery actions, 404/error semantics |

Define desktop and mobile composition separately. Do not merely stack desktop columns. Record content priority, reading order, sticky behavior, overflow, drawer behavior, and the location of the primary action at narrow widths.

## Map visual sections to merchant data

For every proposed section, classify its content owner:

- **catalog:** product, category, price, stock, review, attribute, or related entity data;
- **theme customization:** ordered campaign, carousel, services, or theme-scoped content;
- **CMS:** localized editorial pages and managed HTML;
- **channel:** logo, favicon, locale, currency, home SEO, root category;
- **theme package:** stable interface labels, presentation, tokens, and fallbacks;
- **extension:** payment, shipping, product-type, account, or render-event output.

Keep content in its authoritative system. If merchants need to edit a section, do not bury it in Blade. If an installed customization type cannot represent it clearly, define the custom component contract before implementing its Admin editor and storefront renderer.

Design empty, partial, long, translated, RTL, unavailable, out-of-stock, and error states for dynamic sections. Never make the visual system depend on demonstration data being present.

## Generate Bagisto UI/UX direction

Use `scripts/generate_bagisto_ui_ux.py` for every new visual system or substantial redesign. The engine and its Bagisto-specific knowledge are bundled inside this skill. It makes no network request, imports no other skill, installs nothing, and persists nothing.

The generator:

- builds a multidimensional commerce query from industry, audience, tone, catalog, price position, and optional keywords;
- scores original Bagisto storefront archetypes against the query and `variance`, `motion`, and `density` dials;
- ranks accessible palette and typography strategies without generating a remote font import;
- emits semantic color, spacing, shape, motion, and layering candidates;
- reduces variance, motion, or density where listing, product, cart, checkout, and account tasks require predictability;
- supplies complete page blueprints, responsive policy, interaction policy, content ownership, and anti-generic checks;
- derives Laravel, Vue, and HTML/Tailwind implementation guidance only for stacks discovered in the checkout;
- verifies required palette contrast pairs and reports unresolved runtime or asset approvals; and
- produces a candidate-only `bagisto_review` contract without modifying the project.

Review the complete JSON result. Use `design_system` as one proposal and `alternatives` to challenge it. The generated archetype name is internal vocabulary, not brand copy. Translate it into a concept tied to the real catalog and content.

If the first result is generic or mismatched, adjust one query dimension at a time—tone, catalog, price position, a specific keyword, or one dial—then rerun. Do not raise variance or motion merely to make the design appear more current.

## Filter generated recommendations

Use this sequence with the bundled design generator:

1. Query with product type, industry, audience, price position, catalog shape, emotional tone, and desired density—not only “modern ecommerce.”
2. Review the ranked archetype, palette, and typography alternatives when the initial result is generic or mismatched.
3. Treat suggested styles, palettes, typefaces, layouts, and motion as unapproved candidates.
4. Reject a candidate when its archetype conflicts with the catalog or its page pattern conflicts with a commerce journey.
5. Check every suggested font, image, icon, script, and library against installed dependencies, licensing, privacy, CSP, and performance budgets.
6. Prefer installed CSS/Vue capabilities for motion. Add GSAP or another library only when the user approves the dependency and the measured experience justifies it.
7. Prefer self-hosted licensed fonts when appropriate. Do not add a remote `@import` merely because a generated design system includes one.
8. Translate accepted values into semantic tokens and page decisions; do not paste raw recommender output into production code.
9. Record rejected recommendations and the reason when they materially shaped the decision.

The Bagisto source and approved theme brief remain authoritative after synthesis.

## Review before implementation

Do not begin broad styling until the direction can answer:

1. Why does this archetype fit this catalog and audience?
2. What makes the system identifiable without the logo?
3. Is the primary action obvious on home, listing, product, cart, and checkout?
4. Can every dynamic section handle empty and translated data?
5. Are price, option, stock, error, shipping, and payment states clearer than before?
6. Do mobile composition and RTL work without relying on desktop order or physical left/right assumptions?
7. Are fonts, icons, images, and motion licensed, loadable, and inside budget?
8. Can the system be expressed through reusable tokens rather than page-specific values?
9. Does the design preserve installed Bagisto components and extension seams where they already solve behavior?
10. Can a merchant change intended content without developer intervention?

If the answer is uncertain, narrow the concept or prototype the risky surface before expanding the override set.
