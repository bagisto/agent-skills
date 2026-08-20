# CMS, Channels, and Theme-Customization Data

## Contents

- [Separate the data systems](#separate-the-data-systems)
- [Detect current contracts](#detect-current-contracts)
- [Add a custom administrator component](#add-a-custom-administrator-component)
- [Activate themes by channel](#activate-themes-by-channel)
- [Render theme customizations](#render-theme-customizations)
- [Render CMS pages and channel data](#render-cms-pages-and-channel-data)
- [Seed and migrate data safely](#seed-and-migrate-data-safely)
- [Validate data-driven storefronts](#validate-data-driven-storefronts)

Read this reference when a theme consumes channel settings, homepage customization records, CMS pages, navigation data, or administrator-managed content.

## Separate the data systems

Keep these systems distinct:

| System | Owns | Typical scope |
|---|---|---|
| Theme registry | Theme code, view path, asset settings, optional parent or namespace | Application configuration |
| Channel | Selected theme, hostname, root category, locales, currencies, logo, favicon, home SEO | Storefront channel |
| Theme customization | Ordered content blocks and layout data | Channel plus theme code |
| CMS page | Translated page title, URL key, HTML, SEO, channel assignment | One or more channels |
| Catalog repositories | Categories, products, search, pricing, inventory | Channel, locale, currency, customer group |

Do not hardcode administrator-managed content into Blade when the installed storefront reads it from one of these systems.

Do not confuse selecting a visual theme with creating homepage customization records.

## Detect current contracts

Locate the installed contracts:

```bash
rg -n "theme_code|getCurrentChannel\\(\\)->theme|ThemeCustomization" <discovered-package-roots>
rg -n "home_seo|root_category_id|logo_url|favicon_url" <shop-root> --glob '*.blade.php'
rg -n "PageRepository|shop::cms.page|whereHas\\('channels'" <discovered-package-roots>
```

Read:

- active-theme middleware;
- channel create and edit validation;
- theme customization model and repository;
- administrator theme-customization controller;
- homepage controller and view;
- footer and services components;
- CMS page controller and view.

Derive these values from source:

- supported customization types;
- translated attributes;
- status representation;
- sort field;
- channel and theme filters;
- option schemas;
- upload rules;
- CMS channel-assignment behavior;
- URL rewrite behavior.

Do not embed a fixed list of customization types in reusable automation. Query model constants, controller validation, admin forms, or the installed database schema.

If the requested component is not an installed type, do not insert an arbitrary type value and expect the stock Admin UI to accept or edit it. Read [admin-theme-customization-components.md](admin-theme-customization-components.md) before extending the Admin and storefront contracts.

## Add a custom administrator component

Use an installed component type when it can represent the requested content without a confusing merchant experience. Create a custom type only when the component needs its own structured option schema, editor, validation, or renderer.

Complete `assets/theme-customization-component.contract.template.md` before implementation. It makes the scope, option schema, media policy, Admin extension, cache strategy, and test plan explicit.

Do not confuse this with Shop theme registration. A custom type extends content records for an already registered theme; it does not add the theme to configuration or make it available to a channel.

## Activate themes by channel

This section is callable only from step 7 of the primary workflow. The package registration, theme configuration entry, and any required Vite registry entry must already have been merged without changing a channel. The production build, manifest validation, static validator, and applicable pre-activation runtime gates must then pass before selecting the theme on any channel.

Follow this order:

1. Confirm package registration and merge-only theme/Vite configuration are present while the channel still uses its previous theme.
2. Clear configuration caches when the installed deployment procedure requires it.
3. Confirm the production build, manifest, static validation, and applicable pre-activation runtime gates passed.
4. Record the current channel theme and the source/artifact rollback action.
5. Verify that the admin channel selector lists the new theme.
6. Select and save the theme on a non-production channel only.
7. Request the storefront through that channel's hostname.
8. Verify the active theme code at runtime and execute the post-activation smoke checks.

Keep the global shop default separate from channel activation.

- Change the channel's selected theme to affect that channel.
- Change the global default only to alter fallback behavior.
- Request explicit approval before changing every unconfigured channel's fallback.
- Verify behavior when a channel stores an unknown theme code.

Account for channel context:

- hostname;
- root category;
- default locale;
- allowed locales;
- default currency;
- allowed currencies;
- logo and favicon;
- home SEO;
- inventory sources.

Do not cache one channel's theme or branding in process-global mutable state.

Test each hostname independently when the application serves multiple channels.

## Render theme customizations

Treat customization records as scoped, translated, ordered data.

Filter by the fields used in the installed homepage contract. Common scopes include:

- enabled status;
- current channel ID;
- current channel theme code;
- sort order;
- current locale for translated options.

Preserve all active scopes when replacing the homepage.

Use the model's type constants or an installed type registry instead of repeated string literals.

For every supported type:

1. Inspect its administrator form.
2. Inspect the repository's normalization or upload logic.
3. Inspect the default storefront renderer.
4. Document its option shape locally in tests or typed fixtures.
5. Render missing optional keys defensively.
6. Preserve sort order.
7. Preserve translated values.
8. Preserve responsive image metadata and links.
9. Preserve filter parameters passed to catalog APIs.

Handle common block roles without assuming their availability:

- image carousel;
- product carousel;
- category carousel;
- static HTML and CSS;
- footer links;
- services or feature content.

Render installed types by default. Add a new supported type only through the package-scoped extension workflow in [admin-theme-customization-components.md](admin-theme-customization-components.md), including its Admin editor, validation, renderer, and regression checks.

Keep footer and services queries scoped to both channel and theme when the installed components do so.

Avoid these failures:

- showing blocks from another channel;
- showing blocks created for another theme;
- ignoring disabled records;
- losing administrator sort order;
- reading untranslated raw JSON when a locale translation exists;
- assuming every theme has the same customization records;
- rendering unsanitized content outside the application's established trust model.

When a new theme needs starter records:

- copy data only with user approval;
- replace channel and theme identifiers intentionally;
- preserve translations;
- avoid copying uploaded file paths without copying their storage objects;
- make the operation repeatable without duplicates.

## Render CMS pages and channel data

Keep CMS page routing and data retrieval in controllers or repositories.

Preserve these CMS behaviors when overriding `shop::cms.page`:

- receive the resolved page object;
- require assignment to the current channel when the installed controller does so;
- use the current locale's translation;
- preserve URL rewrite and redirect behavior;
- preserve page SEO fields;
- render the page layout and extension events used by the installed view;
- apply the application's content sanitization and trust policy.

Do not query a CMS page by URL key alone when channels or locales can share keys.

Use channel data instead of literals:

- read the channel logo and favicon with theme fallbacks;
- read home SEO into the title and meta stack;
- build category navigation from the current root category;
- format money through current currency helpers or API resources;
- use locale direction for layout and directional utilities;
- respect channel-specific search, checkout, and catalog configuration.

Keep category data transport compatible with the installed header. If the current storefront serializes a category tree for client use, preserve its shape or replace all consumers together.

Do not store sensitive customer or channel configuration in browser storage.

## Seed and migrate data safely

Separate filesystem scaffolding from database mutation.

Before seeding:

1. Ask whether the user wants content copied, generated, or left empty.
2. Resolve target channel IDs by stable channel code.
3. Resolve the target theme code from configuration.
4. Enumerate locales from the application.
5. Inspect existing records for the same channel and theme.
6. Choose create, merge, or replace semantics explicitly.

Make seeders idempotent:

- use stable natural keys where available;
- update intended records without duplicating blocks;
- keep sort order deterministic;
- avoid deleting administrator content by default;
- wrap multi-record changes in a transaction;
- report created, updated, skipped, and conflicting records.

Keep uploaded media outside database transactions only when storage cleanup is defined.

Do not place environment-specific channel IDs, hostnames, or storage URLs in a distributable theme.

## Validate data-driven storefronts

Build a matrix across:

- every target channel;
- at least two locales, including one right-to-left locale when enabled;
- every enabled customization type;
- empty customization data;
- disabled and reordered records;
- a CMS page assigned to the channel;
- a CMS page not assigned to the channel;
- an existing URL rewrite;
- channel-specific logo, favicon, and home SEO;
- channel root-category navigation.

Assert:

- only matching channel and theme blocks render;
- block order matches administrator order;
- translated content changes with locale;
- fallback content is intentional;
- CMS access respects channel assignment;
- URLs and catalog filters remain valid;
- no content from one channel leaks into another;
- switching the channel theme does not silently reuse incompatible customization data.

Capture database fixtures and rendered output as forward-test artifacts.
