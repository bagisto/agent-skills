# Bagisto storefront coverage matrix

## Contents

- [Classify scope](#classify-scope)
- [Merchant-control coverage](#merchant-control-coverage)
- [Commerce coverage](#commerce-coverage)
- [Quality coverage](#quality-coverage)
- [Evidence rules](#evidence-rules)

## Classify scope

Create a row for every discovered surface. Use `required`, `conditional`, `not-installed`, or `not-enabled`. Do not use `not-applicable` without a concrete discovery result. Installed payment/extension package files create a conditional candidate only; prove provider registration, route/configuration enablement, channel scope and usable sandbox credentials before making the journey required.

Record: feature ID, source of applicability, fixture, spec/test title, environment, result, artifacts, cleanup, and reason for any exclusion. Split one row when channels, locales, currencies, customer states, product types, or extensions behave differently.

## Merchant-control coverage

| Surface | Expected owner | Required proof |
|---|---|---|
| Store name, logo, favicon, contact identity | Channel/configuration | Admin edit, storefront/metadata update, scope isolation, restore |
| Header announcement and navigation | Theme customization/category/CMS | Order, label, link, enabled state, target scope, restore |
| Hero/slider | Theme customization | Copy, image, link, order, status, locale/channel propagation |
| Home product/category blocks | Theme customization + catalog | Admin-selected rules produce correct dynamic items and prices |
| Static promotional sections | Theme customization or CMS | Content, media, CTA and order editable without source change |
| Footer links/services/newsletter | Theme customization/configuration | Admin-controlled content; no unintended duplicate blocks |
| Category page content | Category/attributes | Name, description, image, products, filterable attributes |
| Product content | Product/attributes/inventory | Name, media, price, options, stock and visibility propagation |
| SEO and social metadata | Channel/CMS/category/product | Title, description, canonical/robots and share media as applicable |
| Locale/currency switchers | Channel/locale/currency | Enabled values only; correct persistence, direction and formatting |
| Extension blocks | Owning extension | Enabled-state and data propagation through its supported admin surface |

Treat layout primitives, design tokens, accessible control semantics, and component composition as `code_structure`. Store-specific copy, URLs, selections, contact data, promotions, and images are not structure.

## Commerce coverage

| Area | Minimum behavior | Conditional expansion |
|---|---|---|
| Home/navigation | Header, menus, logo, hero CTA, all visible section links, footer, newsletter | Mega-menu, custom customization types, consent |
| Search | Query, suggestions, result relevance, empty state, special characters, clear/reset | Image/voice search or external search engine if enabled |
| Category | Listing, grid/list, filters, multiple filters, clear, sort, pagination/load-more, empty state | Price slider, layered navigation, custom attributes |
| Product | Gallery, price, tax label, stock, quantity, add to cart, validation | Simple, configurable, grouped, bundle, virtual, downloadable, booking and custom types |
| Cart | Mini-cart, add, update quantity, remove, totals, empty state, coupon apply/remove | Shipping estimate, cart rules, cross-sell, persistent cart |
| Checkout | Guest and customer address, validation, shipping, payment, review, order success | Digital-only, mixed cart, tax zones, multi-address, extension steps |
| Customer | Register, sign in/out, forgot/reset in captured mail, profile, addresses, orders | Downloads, GDPR, social login, impersonation when enabled |
| Engagement | Wishlist, compare, review, newsletter | Share, back-in-stock, product questions when enabled |
| Content | CMS, contact, sitemap/robots where relevant, 404 | Blog, stores, custom landing pages |
| Order lifecycle | Customer order visibility and authoritative created order | Cancel, invoice, shipment, refund, RMA only when enabled and authorized |
| Multi-scope | Channel host/root, locale, currency, RTL, translated content | Multi-inventory, regional tax/shipping/payment |
| Security/session | CSRF-backed forms, auth boundaries, guest/customer isolation | CAPTCHA, consent, rate limits in suitable environments |

Never submit a real payment. Use installed offline methods or documented sandbox credentials.

## Quality coverage

Test representative widths near 390, 768, 1024, and 1440 pixels plus content extremes. Assert behavior, not pixel identity alone: no horizontal overflow, no obscured controls, usable menus/dialogs, correct image sizing, stable loading, and visible focus.

Run automated accessibility checks where the checkout already supports them, then manually spot-check keyboard order, menus, modals/drawers, validation/error association, accessible names, landmarks, headings, alt text, zoom, contrast, and reduced motion.

Measure performance using an agreed environment and budgets. Record LCP, CLS, INP or a defensible lab proxy, transferred image/script/CSS size, caching, and slow API chains. Do not compare noisy development-mode numbers with production budgets.

## Evidence rules

A route render is not feature proof. A checkout row passes only after the intended order-side effect is verified. An admin-control row passes only after the changed value appears in the correct storefront scope and the original value is restored.

Count a skip only when the feature is proven unavailable or disabled. Record how that fact was discovered. Treat missing fixtures, credentials, or selector work as blocked/not proven, not skipped.
