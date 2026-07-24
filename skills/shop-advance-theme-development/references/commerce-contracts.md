# Storefront Commerce Contracts

## Contents

- [Discover the installed contracts](#discover-the-installed-contracts)
- [Preserve page contracts](#preserve-page-contracts)
- [Preserve product contracts](#preserve-product-contracts)
- [Preserve cart contracts](#preserve-cart-contracts)
- [Preserve checkout contracts](#preserve-checkout-contracts)
- [Preserve extension contracts](#preserve-extension-contracts)
- [Run a commerce regression matrix](#run-a-commerce-regression-matrix)

Read this reference before overriding catalog, product, cart, checkout, account, or extension-sensitive views.

## Discover the installed contracts

Treat controllers, routes, API resources, product types, and default Shop views as a single contract set.

Locate them before editing:

```bash
rg -n "return view\\('shop::|->name\\('shop\\." <shop-root> --glob '*.php'
rg --files <shop-root> | rg '/(Http/(Controllers|Resources)|Resources/views)/'
rg -n "view_render_event\\(" <shop-root> <enabled-extension-roots> --glob '*.blade.php'
```

For each surface, record:

- route name and method;
- controller guard and redirect behavior;
- view name;
- variables passed to the view;
- form field names;
- API endpoint names;
- request payload shape;
- response resource class;
- Vue component names and refs;
- render events and parameter keys;
- configuration gates;
- authentication requirements.

Do not infer JSON shape from screenshots. Read the installed resource and controller.

Do not copy route URLs into JavaScript when a route helper is available.

Keep business calculations in backend services and resources. Let the theme render authoritative price, tax, discount, inventory, and eligibility values.

## Preserve page contracts

Keep controller-provided variables intact.

Typical page contracts include:

| Surface | Preserve |
|---|---|
| Home | Channel, ordered theme customizations, visible category tree |
| Category | Category entity, sort, limit, and view-mode parameters |
| Search | Query and filter state, pagination, product resource shape |
| CMS page | Resolved translated page and channel assignment |
| Customer account | Authenticated customer, pagination, permissions, entity status |
| Error page | Status semantics, safe navigation, theme assets |

Verify the exact contract in the installed controller.

Preserve:

- title and meta stacks;
- canonical and social metadata where present;
- structured data;
- breadcrumbs and configuration gates;
- pagination query parameters;
- locale and currency state;
- empty, loading, error, and success states;
- render events surrounding replaceable regions.

When redesigning a page:

1. Keep the original controller and route unless behavior change is explicitly requested.
2. Start from the current view contract.
3. Replace presentation in small sections.
4. Keep a server-rendered fallback for asynchronous data.
5. Preserve accessible headings and landmarks.
6. Test empty and maximum-content cases.

## Preserve product contracts

Treat the product page as a dispatcher for multiple product-type contracts.

Discover present product types from:

- product type classes;
- `products/view/types` view files;
- product form request handling;
- add-to-cart preparation code;
- enabled extension packages.

Do not embed a fixed product-type list in scaffolding. Test every type found in the installed application.

Preserve the base product contract:

- the resolved product entity;
- visibility and status checks performed by the controller;
- URL rewrite behavior;
- localized name, descriptions, and metadata;
- price rendering through product helpers;
- image-gallery resource shape;
- rating and review data;
- additional attributes;
- related and up-sell API endpoints;
- wishlist and compare behavior;
- quantity input;
- add-to-cart form and validation errors.

Preserve type-specific form names.

Examples of fragile fields include:

- variant attribute maps;
- grouped-product quantity maps;
- bundle option and quantity maps;
- downloadable link selections;
- booking date, slot, event, rental, or appointment selections;
- customizable option arrays and uploaded files.

Derive their exact names from current views and backend request parsing.

Do not flatten type-specific forms into a generic product ID and quantity form.

Keep required `enctype`, CSRF tokens, hidden IDs, minimum quantities, and validation rules.

Keep product render events with the same `product` parameter when overriding the view.

Preserve SEO:

- page title fallback;
- description fallback;
- product JSON-LD when enabled;
- Open Graph metadata;
- social-card metadata;
- canonical product URL behavior.

## Preserve cart contracts

Respect the installed cart-page configuration gate.

Use the cart API resource as authoritative state.

Preserve:

- cart item IDs separately from product IDs;
- selected item state;
- item quantity;
- type-specific item options;
- formatted unit and total prices;
- tax-inclusive or tax-exclusive display mode;
- discount and coupon state;
- shipping estimates;
- cross-sell source;
- minimum-order and cart error messages;
- move-to-wishlist behavior;
- mass selection and mass deletion where supported.

Send updates with the exact map shape expected by the current cart API.

Do not recalculate totals in JavaScript.

After a mutation:

1. Consume the returned cart resource or refresh the authoritative endpoint.
2. Update mini-cart and full-cart consumers.
3. Preserve server error messages.
4. Restore the previous valid quantity after a rejected update.
5. Keep loading and disabled states accessible.

Preserve cart render events around:

- header and logo;
- breadcrumbs;
- cart item list;
- image, name, details, quantity, and totals;
- controls;
- summary;
- coupon and shipping estimator;
- mini-cart drawer and actions.

Do not remove an event merely because no installed extension currently renders into it.

## Preserve checkout contracts

Treat checkout as an ordered state machine.

Read the installed checkout controller before rendering the page.

Preserve its entry guards:

- checkout feature availability;
- guest-checkout policy;
- suspended-customer handling;
- cart errors;
- downloadable or non-guest-compatible item restrictions;
- authentication redirects.

Derive the current step order from the installed one-page view and API controller.

A common sequence is:

1. Load cart summary.
2. Collect or select addresses.
3. Collect shipping only when the cart has stockable items.
4. Select payment.
5. Review the final state.
6. Place the order.
7. Follow a payment redirect or success route.

Do not assume that every installed release or extension uses the same steps.

Preserve:

- guest and customer address variants;
- country and state lookups;
- billing-versus-shipping behavior;
- address validation field names;
- shipping-method code;
- payment-method code;
- cart refresh after each state transition;
- order-placement loading lock;
- duplicate-submit prevention;
- server-provided redirect URLs;
- success-page session guard;
- mobile and desktop summaries.

Never trust hidden client totals or method labels as order inputs.

Keep the checkout layout's intentional header, feature, and footer settings.

Keep extension events around header, breadcrumbs, address, shipping, payment, summary, and place-order regions.

Test both carts with and without stockable items.

## Preserve extension contracts

Expect extensions to participate through:

- view render events;
- Laravel lifecycle events;
- service-provider view namespaces;
- payment and shipping registries;
- additional product types;
- Vue components registered before global mount;
- routes and API resources;
- menu or account navigation configuration.

Discover active extensions from registered providers and installed packages.

Before replacing a view:

1. List its render events.
2. Search listeners for those event strings.
3. Search extension views for included components.
4. Search payment and shipping method codes.
5. Search product type registrations.
6. Identify JavaScript registered through pushed scripts.

Preserve extension payload keys exactly.

Do not hardcode a known payment method as the only exceptional flow. Render or branch from installed method metadata and existing extension hooks.

Do not move extension output outside the form, Vue mount root, or checkout step where it expects to operate.

When adding a theme-specific extension point:

- choose a stable event name;
- pass the smallest useful context;
- document placement and ordering;
- render safely when no listener is installed;
- add an integration test with a sample listener.

## Run a commerce regression matrix

Derive the matrix from installed routes and product types, then include at least:

- home with and without customization data;
- category grid and list modes;
- search with filters, sorting, pagination, and no results;
- every installed product type;
- product validation failure;
- add to cart;
- mini-cart update and removal;
- full-cart update, coupon, estimate, and removal;
- guest checkout when enabled;
- authenticated checkout;
- stockable and non-stockable carts;
- each installed shipping carrier;
- each installed payment method;
- payment redirect and failure return;
- order success guard;
- login, registration, account, wishlist, compare, and reviews when enabled;
- one CMS page;
- one extension-injected UI fragment.

Run each relevant flow at desktop and mobile widths.

Include at least one right-to-left locale and two currencies when enabled.

Use only sandbox gateways, test carrier integrations, disposable accounts/orders, and reversible inventory/configuration fixtures. Suppress or capture outbound notifications, webhooks, fulfillment, and external business-system calls. Do not create a real charge or mutate production commerce state without an explicitly approved runbook.

Fail the run on:

- PHP exceptions;
- browser exceptions;
- failed API requests;
- missing assets;
- incorrect route methods;
- lost form fields;
- stale cart totals;
- duplicate order requests;
- absent render-event output;
- inaccessible modal or drawer focus;
- cross-channel or cross-currency data leakage.

Capture request payloads and response shapes for changed flows so future upgrades can identify contract drift.
