# Design and experience quality

## Contents

- [Start with a defensible concept](#start-with-a-defensible-concept)
- [Build a coherent design system](#build-a-coherent-design-system)
- [Design the commerce journey](#design-the-commerce-journey-not-only-the-home-page)
- [Treat responsive behavior as composition](#treat-responsive-behavior-as-composition)
- [Meet accessibility requirements](#meet-accessibility-requirements)
- [Engineer performance into the design](#engineer-performance-into-the-design)
- [Preserve admin control](#preserve-admin-control-and-content-truth)
- [Review quality](#review-quality-before-implementation-completion)

Read this reference for a new visual direction, redesign, component system, or “premium/world-class” request.

## Start with a defensible concept

Create a brief before markup. Read `commerce-design-direction.md`, then copy `assets/theme-brief.template.md` into an approved working plan or reproduce its fields in task notes. Use its vocabulary to make decisions explicit; do not select a style by label alone.

Define:

- brand promise, audience, market, catalog character, price position, and conversion goal;
- a one-sentence visual concept tied to the merchandise;
- explicit anti-goals that rule out generic template choices;
- content availability, localization, channel, and admin-editability constraints;
- measurable accessibility and performance budgets.

Do not infer a luxury, minimalist, playful, or editorial direction merely from the word “best.” Make the direction specific to the supplied brand and products.

## Build a coherent design system

Establish semantic tokens for:

- canvas, surface, elevated surface, text, muted text, border, focus, brand, accent, success, warning, and danger;
- type families, sizes, weights, line heights, tracking, and content measure;
- spacing rhythm, containers, grids, breakpoints, radii, borders, shadows, and z-index;
- duration, easing, transform distance, hover, focus, loading, empty, disabled, selected, error, and success states.

Layer these tokens over compatibility tokens required by inherited Shop templates. Avoid raw colors and one-off spacing where a semantic role exists.

Use typography, composition, imagery, and whitespace to create hierarchy. Avoid indiscriminate gradients, glass panels, oversized pills, interchangeable card grids, and decorative motion that does not reinforce the brand or task.

Record `variance`, `motion`, and `density` from 1–10 with a reason and any page-specific exceptions. Treat recommendation-tool output as candidates; filter fonts, libraries, remote assets, and patterns through installed Bagisto contracts and project constraints before accepting them.

## Design the commerce journey, not only the home page

Make the visual language work across:

- utility bar, header, navigation, search, locale/currency, authentication, and mini-cart;
- home merchandising and admin-managed content;
- category, search, filters, sorting, pagination, empty results, and product cards;
- every enabled product type and its option/availability states;
- product media, price, tax, reviews, quantity, wishlist/compare, add-to-cart, and trust content;
- cart, coupons, estimates, addresses, shipping, payment, order review, success, and failure recovery;
- sign-in, registration, forgotten password, account, addresses, orders, downloads, reviews, wishlist, GDPR/RMA, and extension pages;
- CMS, contact, 404/error, email, loading, empty, permission, and validation states.

Keep primary actions obvious. Preserve price clarity, stock/option feedback, form labels, error recovery, and checkout trust. Never trade commerce comprehension for decorative novelty.

## Treat responsive behavior as composition

Design at content breakpoints, not only named devices.

- Reorder content intentionally when space collapses.
- Preserve tap targets, focus visibility, readable measures, and stable media ratios.
- Test long names, large prices, translated strings, validation errors, empty content, and dense option sets.
- Keep filters, navigation, product actions, cart totals, and checkout progress usable with touch and keyboard.
- Prevent horizontal overflow and avoid viewport-height assumptions on mobile browsers.

## Meet accessibility requirements

Target WCAG 2.2 AA unless the project specifies a stronger target.

- Preserve semantic landmarks, heading order, labels, names, roles, and status announcements.
- Provide full keyboard operation and visible focus.
- Meet text and non-text contrast requirements.
- Do not encode meaning through color alone.
- Provide useful alternative text and decorative-image handling.
- Support zoom, reflow, reduced motion, RTL, and screen readers.
- Keep dialogs, drawers, menus, carousels, tabs, accordions, and validation state accessible.

Use the installed Bagisto components when they already satisfy behavior. Verify rather than assume their accessibility remains intact after styling.

## Engineer performance into the design

- Make the hero/LCP element explicit and stable.
- Reserve media dimensions and avoid late font/layout shifts.
- Limit font families, weights, trackers, third-party scripts, autoplay media, and large carousels.
- Render useful server HTML before client enhancement.
- Keep Vue islands focused; avoid replacing stable Blade output with unnecessary client rendering.
- Use shimmer/loading states without causing layout changes.
- Measure desktop and representative mobile hardware/network conditions.

Set project-specific budgets for LCP, INP, CLS, JavaScript, CSS, image bytes, and request count. A visually polished theme that misses agreed budgets is not complete.

## Preserve admin control and content truth

Prefer channel/theme customization data for content that merchants must manage. Do not hide hardcoded marketing copy inside Blade when administrators need localized editing.

Design graceful behavior for missing images, empty carousels, unpublished categories, unavailable products, and themes with no customization records. Never seed or clone production content destructively.

## Review quality before implementation completion

Review at least:

1. Brand specificity: could this design belong to an unrelated store?
2. Hierarchy: is the next customer action obvious on every key page?
3. Consistency: do components share tokens and states without becoming monotonous?
4. Commerce completeness: are variant, stock, tax, discount, shipping, and error states legible?
5. Accessibility: can keyboard, screen-reader, zoom, contrast, and reduced-motion users complete checkout?
6. Responsiveness: do real content extremes work from small mobile to wide desktop?
7. Performance: do measured budgets pass?
8. Maintainability: can merchants and future developers safely change content and tokens?

Do not approve based only on a home-page screenshot.
