# Localization, SEO, accessibility, and media

Read this reference when changing copy, metadata, direction, images, icons, fonts, or semantic structure.

## Contents

- [Discover supported locales](#discover-supported-locales)
- [Own and register theme translations](#own-and-register-theme-translations)
- [Publish translations only when customization is required](#publish-translations-only-when-customization-is-required)
- [Validate locale parity from the target](#validate-locale-parity-from-the-target)
- [Preserve SEO contracts](#preserve-seo-contracts)
- [Maintain semantic and assistive behavior](#maintain-semantic-and-assistive-behavior)
- [Use media responsibly](#use-media-responsibly)
- [Fonts and icons](#fonts-and-icons)
- [Brand email without importing the storefront runtime](#brand-email-without-importing-the-storefront-runtime)
- [Minimum checks](#minimum-checks)

## Discover supported locales

Inspect the target checkout before creating language files. Derive the required locale set from the installed Shop/package locale directories, enabled channel locales, fallback configuration, and repository policy. Treat repository policy as authoritative when it requires more locales than the currently enabled channels. Do not embed a locale count, assume a canonical locale, or assume English-only content.

For each required locale, keep theme-owned interface translations inside the theme package:

```text
<theme-package>/
└── src/Resources/lang/
    └── <discovered-locale>/
        └── app.php
```

- Derive `<discovered-locale>` and the translation file inventory from the target; preserve locale identifiers exactly, including case and region separators.
- Select the canonical/fallback locale from the target's configuration or repository policy. Do not hardcode one in the skill or generator.
- Add, rename, or remove each package-owned key across every required locale in the same change.
- Keep nested file names and key shapes identical across locales unless the target explicitly documents an exception.
- Test at least one locale with long strings and every enabled text direction; do not infer direction from a short fixed list when the checkout already exposes direction metadata.

Do not invent translations silently for a production launch. Surface missing professional translations and deliberate fallback-only locales as explicit release requirements.

## Own and register theme translations

A distributable theme package must own its copy. In the package service provider's `boot()` method, register its language root with a stable, package-specific namespace:

```php
$this->loadTranslationsFrom(
    __DIR__ . '/../Resources/lang',
    '<translation-namespace>',
);
```

Discover or derive `<translation-namespace>` from the package identity and keep it stable across releases. It must be collision-resistant and must not reuse a core namespace or a generic name such as `shop` or `theme`. Reference theme strings with fully namespaced keys, for example:

```blade
{{ __('<translation-namespace>::app.storefront.navigation.open-menu') }}
```

Use descriptive, hierarchical keys that describe meaning rather than the current wording. Apply the same namespace to Blade, PHP, configuration, email, and Vue/JavaScript integration supported by the installed frontend localization plugin.

Never add theme copy to or edit translations under the installed Shop package. Never patch a dependency's language files to make a theme work. Do not hardcode customer-visible interface copy in Blade, Vue, JavaScript, or package configuration. Reuse an existing Shop key only when the meaning is exactly the same; otherwise add a namespaced key owned by the theme package. Merchant-managed, catalog, CMS, and channel content must continue through their installed localized data models rather than being converted into package translations.

An overlay without its own service provider cannot register new package translations. It may reuse semantically matching installed keys; if it needs original interface copy, promote it to a package-owned theme instead of modifying Shop translations.

## Publish translations only when customization is required

Package translations work through `loadTranslationsFrom()` and do not need to be published for normal operation. Offer publishing only when operators must override theme wording:

```php
$this->publishes([
    __DIR__ . '/../Resources/lang' => lang_path('vendor/<translation-namespace>'),
], '<translation-namespace>-translations');
```

First inspect the installed Laravel/Bagisto convention and use its effective vendor-language destination if it differs. Keep the destination namespace and publish tag package-specific. Before publishing:

1. resolve and report the exact source and destination;
2. inventory destination collisions;
3. preserve operator-owned overrides;
4. require explicit approval for any replacement; and
5. avoid forced publishing as an installation or upgrade default.

Publishing must remain optional and collision-safe. Updating the package must not overwrite previously published operator translations.

## Validate locale parity from the target

Derive validation commands from the checkout rather than assuming that a named Artisan command exists or covers third-party packages.

1. Discover the required locales and canonical locale from channel/configuration/repository policy.
2. Enumerate every package-owned translation file and recursively flatten its keys.
3. Compare file inventory, nested key paths, PHP syntax, and value types across all required locales.
4. Run the repository-approved translation consistency command when available; inspect its help and scope it to the theme package when supported.
5. Add a package-level parity test when the repository command does not discover the theme package.
6. Render representative namespaced keys in each required locale and fail when a raw key, wrong namespace, or unintended fallback appears.
7. Verify locale switching, translated validation/checkout states, long-string reflow, and every enabled RTL direction.

Keep Blade/Vue validation messages connected to the installed localization plugin, and localize database-driven theme customization data according to the installed model schema. Report intentionally untranslated values and fallback behavior; do not disguise missing parity as a passing check.

## Preserve SEO contracts

- Keep channel home SEO and per-page meta slots.
- Preserve canonical, base URL, robots, structured data, pagination, social, and alternate-language behavior found in installed views.
- Use one meaningful page heading and a logical heading hierarchy.
- Keep product/category names and descriptions server-rendered where possible.
- Avoid duplicate content introduced by filters, sorting, or theme-specific routes.
- Validate title, description, canonical, language, direction, status, and structured data on representative pages.

## Maintain semantic and assistive behavior

- Preserve the master layout's skip link, landmarks, language, direction, focus order, and live regions.
- Use real buttons for actions and links for navigation.
- Give inputs persistent labels, instructions, autocomplete, and error associations.
- Announce async cart, validation, filter, and checkout changes appropriately.
- Trap and restore focus for modal interfaces.
- Make hover-only information available to touch, keyboard, and screen-reader users.

## Use media responsibly

- Obtain product and campaign media from authorized sources.
- Provide intrinsic width/height or aspect ratio.
- Write contextual alternative text; use empty alt text for decoration.
- Use `picture`/`srcset` or installed Bagisto media helpers where their current signatures fit.
- Prioritize only the likely LCP image and lazy-load below the fold.
- Avoid converting product color/details in ways that misrepresent merchandise.
- Verify image-cache/resizing behavior, storage URLs, placeholders, and broken media.

## Fonts and icons

- Confirm font licenses and supported scripts.
- Limit files and weights; use fallbacks with compatible metrics.
- Preload only critical font files.
- Preserve icon mappings used by inherited components.
- Give interactive SVGs accessible names and decorative SVGs appropriate hiding.

## Brand email without importing the storefront runtime

Discover the installed mail view namespace, layout component, variables, and theme-resolution behavior before overriding an email.

- Preserve order, invoice, shipment, refund, customer, and extension data variables.
- Use email-safe markup and inline-compatible CSS; do not depend on storefront Vite, Vue, JavaScript, web fonts, or interactive components.
- Keep transactional meaning, legal text, totals, addresses, payment/shipping details, and plain-text/link fallbacks intact.
- Localize subjects and body copy through the installed translation path.
- Test generated mail through the configured local mail sink and representative desktop/mobile clients.
- Verify absolute asset URLs and accessibility of headings, tables, links, and alternative text.

## Minimum checks

Test:

- LTR and RTL;
- locale and currency switching;
- translated validation and checkout;
- 200%/400% zoom and text reflow;
- keyboard-only purchase journey;
- screen-reader labels/status for navigation, filters, product options, cart, and checkout;
- metadata/structured data on home, category, product, CMS, and error pages;
- mobile/desktop LCP, CLS, and broken-media requests.
