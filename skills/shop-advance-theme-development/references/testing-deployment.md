# Testing, deployment, and upgrades

## Contents

- [Use layered gates](#use-layered-gates)
- [Activate safely](#activate-safely)
- [Deploy atomically](#deploy-atomically)
- [Audit upgrades](#audit-upgrades)
- [Completion evidence](#completion-evidence)

Read this reference before claiming completion, activation, deployment, or upgrade compatibility.

## Use layered gates

### Static and configuration

1. Run `inspect_theme_environment.py` and retain the output.
2. Run `validate_theme.py` for the target theme/package.
3. Validate JSON, PHP syntax, Composer metadata, PSR-4/provider registration, and theme config.
4. Run repository formatting/lint commands for changed PHP/JS/CSS.
5. Run translation consistency checks when keys or locale files change.

### Asset build

1. Use the checkout-approved package manager and lockfile policy.
2. Run the theme's production build.
3. Validate CSS and JavaScript entries in the Vite manifest.
4. Check every emitted asset request for success.
5. Ensure no hot marker controls a production-like run.
6. Compare output size against agreed budgets and baseline.

### Laravel and feature tests

Run affected package/application tests. Include assertions for theme selection, namespace fallback, parent resolution, view renderability, and relevant endpoints where the test architecture allows it.

Do not delete or weaken tests to make a theme pass.

### Browser journeys

Use the target repository's Shop Playwright harness when present. Adapt `assets/storefront-smoke.template.spec.ts` only as a supplement.

Capture page exceptions, console errors, failed requests, HTTP status, and screenshots/traces on failure. Exercise:

- home and merchant-managed customization blocks;
- category, search, filters, sorting, pagination, and empty state;
- each enabled product type and representative options;
- mini-cart, cart updates, coupon, estimates, and removal;
- guest and customer checkout through at least one enabled payment/shipping path;
- authentication, account, addresses, orders, downloads, reviews, wishlist, and compare;
- CMS, contact, 404/error, GDPR/RMA and enabled extension pages;
- locale, currency, multi-channel, and RTL combinations;
- mobile navigation and responsive content extremes.

Test render-event integrations, especially payment UI, after changing the master layout.

If an intentionally unavailable third-party endpoint must be excluded from the supplemental smoke template, scope `THEME_SMOKE_IGNORED_RESPONSE_URLS` to the narrowest reviewed URL pattern and report the exclusion; never suppress same-origin asset/API failures broadly.

Set `THEME_SMOKE_READY_SELECTOR` to a checkout-derived, stable post-hydration signal when the page exposes one. Keep `THEME_SMOKE_OBSERVATION_MS` bounded and long enough to observe deferred Vue/API failures; the template rejects values above its safety cap. A visible `<main>` at DOM readiness is not sufficient evidence that asynchronous startup stayed healthy.

Run mutating journeys only in an isolated test environment. Use sandbox payment credentials and test carriers; disable or capture outbound email, SMS, webhooks, ERP/CRM calls, and fulfillment jobs; create disposable customers/orders; record and restore inventory, coupons, and configuration. Never submit a real charge or place a production order unless the user supplies an approved production runbook and explicit authorization. Production smoke tests stop before irreversible submission by default.

### Accessibility and performance

Run automated accessibility checks and complete keyboard/screen-reader spot checks. Measure Core Web Vitals under representative mobile and desktop conditions. Treat automated tools as evidence, not complete proof.

## Activate safely

1. Build and validate package code and assets.
2. Confirm theme customization content exists or degrades gracefully for the target channel/theme code.
3. Record current channel theme and rollback steps.
4. Select the new theme only on the requested channel.
5. Clear/rebuild relevant config, view, response, and application caches according to the deployment environment.
6. Reload long-running workers/Octane when required.
7. Run production smoke tests.
8. Roll back the channel selection and matching artifact release together if a gate fails.

Do not silently change `shop-default`. Do not activate every channel. Do not activate before the matching manifest is deployed.

## Deploy atomically

- Deploy PHP/views/config and their exact built assets as one release.
- Exclude development hot markers, Node modules, test artifacts, and local symlinks.
- Verify published views or namespace registration on the deployed filesystem.
- Warm caches only after code/config is in place.
- Keep rollback artifacts for both source and public build output.
- Verify CDN/cache invalidation when asset URLs or HTML references change.

## Audit upgrades

Run `diff_theme_overrides.py` before and after changing the installed Bagisto/Shop version.

- Review modified overrides against the new upstream file.
- Remove identical copies that no longer need ownership.
- Port upstream security, accessibility, performance, component, event, and API changes.
- Rebuild assets from the new installed Shop contract.
- Update the override baseline with new source hashes only after tests pass; inspect the complete preview with `snapshot_upgrade_baseline.py --refresh --json`, then explicitly use `--refresh --apply --acknowledge-reviewed`.
- Re-run the complete commerce and extension matrix.

For a legacy theme with no accepted baseline, review the complete current diff first. After reconciliation and all applicable tests pass, use `snapshot_upgrade_baseline.py --json` in dry-run mode, inspect its theme-owned hashes and complete Shop view/asset/discovered-build-contract inventory, then repeat with `--apply --acknowledge-reviewed`. Never snapshot an unexplained or untested upstream state. The baseline intentionally excludes Shop PHP and runtime data contracts, so keep the Bagisto release check and PHP/browser regression suites mandatory. Treat future required baseline-field changes as schema migrations: increment `schema_version`, document the migration, and never silently accept an older partial document.

For a full fork, treat every added, removed, or changed upstream source as a review item. For a sparse overlay, inspect overridden views plus every upstream inventory change that could alter inherited output.

## Completion evidence

Report:

- mode and theme identity;
- exact changed files;
- installed Bagisto/frontend baseline used;
- build/manifest results;
- formatting, translation, PHP, feature, browser, accessibility, and performance results;
- channels/locales/product types/extensions exercised;
- skipped checks and risk;
- activation state and rollback procedure;
- upstream override-diff summary.

Do not use “looks good” as completion evidence.
