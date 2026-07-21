---
name: bagisto-theme-testing
description: Audit and prove Bagisto storefront themes with source inspection, ownership mapping, admin-to-storefront mutation tests, and Playwright commerce journeys. Use when checking that visible content is dynamic and merchant-controlled; validating theme customizations, channels, CMS, categories, products, search, filters, cart, checkout, accounts, locales, currencies, responsive behavior, accessibility, runtime errors, or enabled extensions; or deciding whether a Bagisto theme is safe to activate or release.
---

# Bagisto Theme Testing

Prove that a theme is merchant-usable and preserves the installed Bagisto commerce runtime. Treat “dynamic,” “working,” and “all functionality” as evidence claims, never visual assumptions.

## Non-negotiable rules

- Read the target repository instructions and the parent Bagisto theme skill before acting.
- Derive the Bagisto version, theme code, channel, locale, routes, packages, product types, extensions, Playwright configuration, credentials, and commands from the checkout.
- Reuse safe parts of the installed Shop and Admin Playwright harnesses, fixtures, page objects, and seeded-data conventions. Audit inherited mutating helpers first; do not run a spec that relies on hardcoded IDs, mutates an arbitrary first record, lacks cleanup, bypasses the mutation opt-in, or targets another theme/channel.
- Run state-changing tests only in an isolated test environment. Never change production content, place a real charge, send real messages/webhooks, or trigger fulfillment.
- Obtain explicit authorization before seeding data or changing admin configuration. Record original values and restore them in `finally`, teardown, or an equally reliable cleanup path.
- Use sandbox/offline payment and test shipping methods. Stop before irreversible submission in a production smoke run.
- Do not weaken assertions, broadly suppress network failures, use arbitrary sleeps as synchronization, or mark a failing feature skipped to obtain a green run.
- Never claim exhaustive coverage. Inventory installed and enabled surfaces, map each to evidence, and report every justified exclusion and residual risk.
- Treat screenshots as visual evidence only. Screenshots cannot prove admin ownership, persistence, calculations, inventory, authorization, or checkout correctness.

## 1. Discover the installed test surface

Resolve `<testing-skill-dir>` from this file and `<parent-skill-dir>` three directories above its `scripts/` directory. Run the parent environment inspector first, then this module's read-only inventory:

```bash
python3 <parent-skill-dir>/scripts/inspect_theme_environment.py \
  --project-root <project-root> \
  --theme-code <theme-code> \
  --json

python3 <testing-skill-dir>/scripts/inspect_bagisto_test_surface.py \
  --project-root <project-root> \
  --theme-code <theme-code> \
  --json > <project-test-artifacts>/bagisto-theme-test-surface.json
```

Review the discovered Shop/Admin harnesses, registered product types, checkout scenarios, conditional installed packages/payment methods/shipping carriers, mutation-risk candidates, theme view root, Blade signals, and hardcoding candidates. A candidate is a review lead, not proof of a defect. Do not confuse a mixed-cart scenario filename with a registered product type, and do not treat a configuration default or installed extension/payment package as effectively enabled until runtime/channel configuration proves it.

Read [coverage-matrix.md](references/coverage-matrix.md) and classify every row as required, conditional, not installed, or not enabled. A feature is in scope when the checkout, configuration, route, customization type, product type, channel, or enabled extension exposes it.

## 2. Build the ownership contract

Copy [theme-ownership-manifest.template.json](assets/theme-ownership-manifest.template.json) into the project test area and adapt it. Do not add a project documentation file merely to hold test evidence.

Inventory every customer-visible content surface, including header, navigation, announcement, logo, hero, home sections, category/product merchandising, promotional copy, footer, newsletter, contact details, and SEO/media fields. Assign one authoritative owner:

- `theme_customization`
- `channel`
- `configuration`
- `cms_page`
- `category`
- `product`
- `locale`
- `extension`
- `derived_commerce`
- `code_structure`

Use `code_structure` only for non-editorial structure such as layout composition, spacing, accessible control markup, and design tokens. Do not use it for store-specific copy, destinations, catalog selections, contact information, promotional images, or merchandising content.

Read [dynamic-admin-control.md](references/dynamic-admin-control.md). Prove dynamic ownership with four linked facts:

1. source binding from the authoritative Bagisto record/configuration to the view;
2. an isolated admin edit containing a unique run marker;
3. storefront propagation in the correct theme, channel, and locale without a source edit;
4. restoration of the original value plus isolation from non-target scopes.

Validate the manifest:

```bash
python3 <testing-skill-dir>/scripts/validate_ownership_manifest.py \
  --manifest <manifest.json> \
  --inventory <project-test-artifacts>/bagisto-theme-test-surface.json \
  --strict-admin-control
```

Pass `--require-journey <id>` for each conditional extension, payment, shipping, channel, locale, currency, or customization journey proven enabled after the inventory was generated.

Do not call a surface dynamic because it contains Blade variables or a loop. Server-rendered hardcoded arrays, translation-backed marketing copy, and fixed asset paths can still be non-editable.

## 3. Plan layered Playwright evidence

Read [playwright-engineering.md](references/playwright-engineering.md) and [test-data-safety.md](references/test-data-safety.md). Build one coverage record for every applicable journey. Prefer existing Bagisto specs only after their fixture lifecycle passes this skill's safety rules, then extend the theme-specific gaps.

Use four layers:

1. **Runtime contract:** status, page errors, console/Vue failures, same-origin failures, broken media, hydration, semantic landmarks, and stable routes.
2. **Admin propagation:** mutate approved content/configuration, save, observe storefront, verify scope isolation, and restore.
3. **Commerce behavior:** search, suggestions, category, filters, sorting, pagination, product types/options, pricing, inventory, mini-cart, cart, coupon, checkout, payment/shipping, auth, account, wishlist, compare, review, CMS, and enabled extensions.
4. **Experience quality:** desktop/mobile/RTL layouts, keyboard paths, focus, automated accessibility, reduced motion, and measured performance budgets.

Adapt [runtime-contract.template.spec.ts](assets/runtime-contract.template.spec.ts) for missing cross-route health coverage. Adapt [admin-storefront-propagation.template.spec.ts](assets/admin-storefront-propagation.template.spec.ts) only after discovering the installed Admin form and stable selectors. Templates supplement the checkout; they do not replace its tests.

## 4. Implement reliable tests

- Create deterministic fixtures through existing Bagisto admin helpers, factories, seeders, or test APIs. Give records a unique run ID.
- Test each enabled product type using a representative purchasable fixture. Cover option validation and price/stock effects, not merely page rendering.
- Use role, label, text, form name, route, or purpose-built `data-testid` locators. Keep test-only attributes semantic and package-scoped.
- Synchronize on URL, response, visible state, toast, spinner completion, or DOM condition. Avoid `waitForTimeout` except for a documented bounded observation window that detects deferred runtime failures.
- Assert both customer-visible results and authoritative effects where practical: cart line/totals, order creation, stock transition, account order visibility, admin status, and scope-specific content.
- Attach traces, screenshots, videos, console failures, failed requests, and relevant identifiers on failure. Never place passwords, tokens, payment data, or customer secrets in artifacts.
- Make tests order-independent unless the installed suite explicitly defines a serial fixture lifecycle. Clean up created records or use a disposable database reset owned by the repository.

## 5. Run by risk tier

Derive exact commands from the discovered package scripts and Playwright configs.

- **Pull request:** static validation, build, runtime smoke, changed-surface propagation tests, affected commerce specs, desktop and mobile Chromium.
- **Release candidate:** full applicable Shop/Admin matrix, every enabled product type and extension, customer and guest checkout, locale/currency/RTL matrix, accessibility, and performance.
- **Post-deployment:** read-only runtime/asset/navigation checks; stop checkout before order placement unless an approved production runbook explicitly authorizes more.

List tests before a long run and reject accidental `test.only`, unexpected skips, empty projects, or zero matching tests. Preserve the checkout's reporter and failure artifacts.

## 6. Gate completion

Require all of the following:

- every visible content surface has an ownership classification;
- every merchant-controlled surface has passing save → storefront → restore evidence;
- every installed and enabled commerce journey is covered by a passing test or a reviewed exclusion;
- no unexplained page error, console/Vue error, same-origin failed request, broken asset, or failed API response remains;
- responsive, keyboard, accessibility, locale/RTL, and performance checks meet the agreed targets;
- the production build and relevant PHP/translation tests pass;
- no live theme/channel activation occurs before the gates pass.

Report exact commands, environment, theme/channel/locale, fixtures, passed and failed specs, applicable rows, exclusions, artifacts, cleanup/restoration, and residual risk. Say “not proven” whenever evidence is missing.
