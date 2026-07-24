# Playwright engineering for Bagisto themes

## Contents

- [Reuse the checkout](#reuse-the-checkout)
- [Design stable tests](#design-stable-tests)
- [Test runtime integrity](#test-runtime-integrity)
- [Test commerce effects](#test-commerce-effects)
- [Control the matrix](#control-the-matrix)

## Reuse the checkout

Discover `packages/Webkul/Shop/tests/e2e-pw` and `packages/Webkul/Admin/tests/e2e-pw` or their installed equivalents. Reuse their `playwright.config`, setup fixture, authenticated storage state, page objects, product creation helpers, and report paths.

Audit existing Bagisto feature specs before running them. An upstream/example spec is reusable only when its target records, theme/channel scope, mutation opt-in, cleanup, credentials and external side effects are safe for the selected environment. Replace hardcoded IDs/theme codes and arbitrary “delete first record” helpers with test-owned identifiers and exact cleanup. Theme work most often needs supplemental coverage for changed selectors/layouts, runtime errors across representative routes, merchant-control propagation, responsive navigation, accessibility, and visual regression.

Do not copy all upstream specs into a theme package. That creates stale coverage. Invoke only the reviewed upstream suite and keep theme-specific specs small.

## Design stable tests

- Prefer accessible role/name and label locators. Use exact route/form names or scoped `data-testid` when no stable accessible locator exists.
- Avoid generated CSS utility classes, DOM depth, `.nth()` without a semantic scope, localized display strings in multi-locale tests, and assumptions such as a `mens` category or `simple` product name.
- Discover or create records by unique SKU/code/run ID. Do not select the first catalog item unless the fixture owns the result set.
- Wait for observable state: response, URL, saved toast, dialog state, spinner removal, cart badge/totals, or order success identifier.
- Verify loading, success, empty, validation-error, API-error, disabled and out-of-stock states when applicable.
- Keep assertions close to the behavior that caused them. Record the route, SKU, customer, order and channel codes in failure attachments without secrets.

Use projects for meaningful dimensions rather than multiplying every combination. Cover all critical journeys in the primary channel/locale, then targeted locale/currency/RTL/responsive cases for scope-sensitive behavior.

## Test runtime integrity

For each representative route, collect from before navigation until a bounded post-hydration observation completes:

- uncaught page exceptions;
- console errors and Vue warnings;
- failed requests;
- same-origin HTTP 4xx/5xx responses;
- broken visible images and invalid primary links;
- missing `lang`/`dir`, main landmark and page title;
- horizontal overflow at tested viewport widths.

Allow only narrow, reviewed third-party exclusions. Never suppress all failed requests, all 404s, or all console errors. Prefer route-specific readiness selectors when the app exposes them.

## Test commerce effects

Assert server-authoritative outcomes, not only clicks:

- search: URL/query plus intended fixture result and empty state;
- filters/sort: selected state plus product-set/order change based on controlled fixture values;
- product: option validation, displayed price, quantity limits, stock and correct configured line item;
- cart: line identity, unit/line price, quantity, discount, tax/shipping estimate and total recomputation;
- checkout: address validation, chosen shipping/payment, review totals, success ID and authoritative order record/account history;
- inventory/order lifecycle: expected stock/order transition for the configured product and payment method;
- auth/account: session boundary, persistence and owner-only data;
- wishlist/compare/review: correct customer/product association and removal/update behavior.

Use response inspection to improve diagnosis, but do not couple every test to private API details unless those APIs are part of the installed frontend contract.

## Control the matrix

Before a long run:

1. list discovered tests;
2. fail CI on `test.only` or unexpected skips;
3. confirm at least one expected test matched each required feature tag/path;
4. run serially when shared Bagisto fixtures demand it;
5. retain trace/video/screenshot only according to repository policy;
6. archive a machine-readable coverage/ownership manifest with the report.

Shard only independent tests. Admin mutation tests touching the same customization, channel, configuration, coupon or inventory record must not race.
