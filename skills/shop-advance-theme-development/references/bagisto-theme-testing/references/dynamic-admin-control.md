# Dynamic and admin-control proof

## Contents

- [Classify ownership](#classify-ownership)
- [Test the full propagation chain](#test-the-full-propagation-chain)
- [Audit every visible section](#audit-every-visible-section)
- [Recognize false proof](#recognize-false-proof)

## Classify ownership

Use one primary owner per surface:

- `theme_customization`: image/category/product carousels, footer links, services, static sections, or package-defined customization types;
- `channel`: theme selection, hostname/root, locale/currency set, logo and channel identity where supported;
- `configuration`: supported core configuration exposed through Admin;
- `cms_page`: merchant-authored pages and linked landing content;
- `category`: category identity, description, image, hierarchy, products and filterable attributes;
- `product`: media, localized content, pricing, inventory, variants/options and visibility;
- `locale`: translated UI labels owned by localization files or an installed translation system;
- `extension`: content or behavior owned by an enabled package;
- `derived_commerce`: totals, tax, promotions, stock state and other server-authoritative calculations;
- `code_structure`: non-editorial markup, responsive layout, components, tokens and interaction mechanics.

If content should be editable but the installed Bagisto Admin has no suitable owner, implement a package-scoped customization type/editor using the parent skill's contract. Do not modify core Admin/Theme packages for convenience.

## Test the full propagation chain

For each merchant-controlled surface:

1. Select an isolated channel, locale and theme customization record.
2. Read and retain the original value and status.
3. Create a unique marker such as `E2E-HERO-<run-id>` and an approved test asset/link where needed.
4. Change the value through the installed Admin UI or an existing test helper that exercises the same application contract.
5. Assert the save succeeds and the persisted edit page shows the marker.
6. Open a fresh storefront context, bypass only documented caches, and verify the marker at the intended selector/route.
7. Verify a non-target locale or channel did not change when scoping applies.
8. Restore the exact original value/status in `finally` or teardown.
9. Open another fresh storefront context and verify restoration.

If cache invalidation is part of normal Bagisto behavior, the test must prove it. Do not clear all caches manually between save and storefront verification unless that is the documented production workflow being tested.

For uploaded media, record the original media reference, upload a test asset through Admin, verify the storefront request succeeds with the correct responsive/alt behavior, restore the original reference, and clean up only the test-owned media if the application supports safe deletion.

## Audit every visible section

Build the surface list from rendered pages and source together:

- enumerate semantic sections and stable identifiers from desktop and mobile pages;
- map each section to the Blade/Vue component and its input;
- trace the input to repository/model/configuration/customization ownership;
- verify no static fallback masks an empty or disabled admin record;
- verify order, status, locale, channel and link settings where supported;
- verify product/category blocks use current catalog state rather than embedded arrays;
- identify duplicate renderers such as two newsletter blocks or repeated footer content.

Keep a `code_structure` surface for intentional fixed structure. The strict validator rejects editorial `code_structure` ownership, not legitimate theme composition.

## Recognize false proof

These are insufficient:

- a Blade variable exists, but its value comes from a hardcoded PHP array;
- a string uses a translation key, but the merchant cannot edit the intended marketing content;
- an image uses `bagisto_asset()`, but the asset is fixed in source;
- a carousel loops dynamically, but the selected products/categories are fixed or unrelated;
- an Admin record saves, but the active channel/theme does not render it;
- the storefront changes only after a source edit, seeder rerun, or manual global cache purge;
- a screenshot contains the expected text without proving the source, scope, save, or restore path.
