# Storefront context (regions, currencies, locales, CMS, themes)

The read-only reference feeds every storefront leans on but rarely thinks about: the country/state lists behind address forms and shipping estimates, the channel/currency/locale selectors in the header, the policy links in the footer, and the configurable content blocks on the homepage. All public (storefront key only), all cacheable, none of them mutate.

> **Source of truth:** open each endpoint's docs page below for the exact response before rendering. Don't hardcode these — fetch them, because they're store-configured and change per deployment.

| Feed | REST | GraphQL field | Docs |
|------|------|---------------|------|
| Countries | `GET /api/shop/countries` (+ `/{id}`) | `countries` / `country` | [countries](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-countries) · [country](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-country) · [REST](https://api-docs.bagisto.com/api/rest-api/shop/countries/get-countries) |
| Country states | `GET /api/shop/countries/{country_id}/states` · `GET /api/shop/country-states` (+ `/{id}`) | `countryStates` / `countryState` | [country-states](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-country-states) · [country-state](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-country-state) · [REST](https://api-docs.bagisto.com/api/rest-api/shop/countries/get-country-states) |
| Channels | `GET /api/shop/channels` (+ `/{id}`) | `channels` / `channel` | [channels](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-channels) · [channel](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-channel) · [REST](https://api-docs.bagisto.com/api/rest-api/shop/channels/get-channels) |
| Currencies | `GET /api/shop/currencies` (+ `/{id}`) | `currencies` / `currency` | [currencies](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-currencies) · [currency](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-currency) |
| Locales | `GET /api/shop/locales` (+ `/{id}`) | `locales` / `locale` | [locales](https://api-docs.bagisto.com/api/graphql-api/shop/locales/queries/locales) · [single-locale](https://api-docs.bagisto.com/api/graphql-api/shop/locales/queries/single-locale) · [REST](https://api-docs.bagisto.com/api/rest-api/shop/locales/get-locales) |
| CMS pages | `GET /api/shop/pages` (+ `/{id}`) | `pages` / `page` | [pages](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-pages) · [page](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-page) |
| Theme blocks | `GET /api/shop/theme-customizations` (+ `/{id}`) | `themeCustomizations` / `themeCustomization` | [theme-customisations](https://api-docs.bagisto.com/api/graphql-api/shop/queries/theme-customisations) · [single](https://api-docs.bagisto.com/api/graphql-api/shop/queries/single-theme-customisation) · [REST](https://api-docs.bagisto.com/api/rest-api/shop/theme-customizations/get-theme-customizations) |

- **Auth:** `X-STOREFRONT-KEY` only — all public.
- **Cache aggressively.** These rarely change within a session — fetch once (ideally server-side at load / build) and reuse; revalidate occasionally, not per interaction.
- Currencies and CMS pages have **GraphQL docs only**; for those two over REST, mirror the same fields against the live endpoint.

---

## Countries & states (address forms, shipping estimates)

Drive every country `<select>` from `GET /api/shop/countries`; when a country is chosen, load its states from `GET /api/shop/countries/{country_id}/states` (or the flat `/api/shop/country-states`) and populate the state field. Used by address forms, the address book, and shipping estimates (see [checkout](../flows/checkout.md) / [account](../flows/account.md)).

- **Dependent dropdowns:** disable/clear the state field until a country is chosen; fetch states on country change. Some countries have no states — fall back to a free-text field.
- Cache the country list app-wide; cache states per country.

## Channel / currency / locale selectors (the header)

- **Channel** = the storefront context (catalog, currencies, locales, root category). `channels` lists what's available; the selected channel scopes the rest. Most storefronts pick one channel via config and don't expose a switcher — only surface a selector if the store genuinely runs multiple channels.
- **Currency** — `currencies` lists the channel's allowed currencies. The selector sets the display currency; pass the chosen currency/channel/locale through to catalog calls so prices come back formatted correctly (don't format prices client-side — render the API's `formatted*` fields).
- **Locale** — `locales` lists the available languages (with `direction` for LTR/RTL). The selector sets the language and must drive your RTL layout when `direction` is `rtl`.

Render these as compact header dropdowns (often grouped in a "region/language" menu). Persist the user's choice and re-fetch the catalog in the new currency/locale.

## CMS pages (footer policy links, static pages)

`GET /api/shop/pages` returns the store's CMS pages (About, Privacy, Terms, Shipping policy, …); `GET /api/shop/pages/{id}` (or the by-url-key query) returns one page's content. Use the list to build **footer navigation** and render each page on its own route.

- Page content is **store-authored HTML** — render it inside a styled content container and sanitise if you don't fully trust the source.
- Pages carry per-locale translations; request the active locale so the right language renders.

## Theme customizations (homepage blocks)

`GET /api/shop/theme-customizations` returns the configurable homepage/storefront blocks (image carousels, product carousels, static-content snippets, footer link sets, etc.), filterable by `?type=`. Each entry carries its type + per-locale options. Build the homepage by iterating the returned blocks in order and rendering a component per `type` — so merchants can re-arrange the homepage from the admin without a code change.

`translation.options` is a **JSON-encoded string** — `JSON.parse` it client-side. Shape per `type`:

- `image_carousel` → `{ images: [{ image, link, title }] }` — render inline
- `product_carousel` → `{ title, filters: { new, featured, limit, sort } }` — forward `filters` to the products listing, render the returned products
- `category_carousel` → `{ title, filters: { parent_id, limit, sort } }` — `parent_id` → `treeCategories(parentId:)`, render the returned categories
- `static_content` → `{ html, css }` — inject inline (images use `data-src`, not `src`)
- `footer_links` → `{ column_1: [{ url, title, sort_order }], … }`
- `services_content` → `{ services: [{ service_icon, title, description }] }`

Image/static/footer/services blocks are self-contained; `product_carousel` and `category_carousel` are only config — their `filters` point at the products / categories endpoints you must call. Content is locale-specific: pass `X-Locale` to select the `translation` locale (else store default); `translations[]` carries every locale.

- Render an unknown/unsupported `type` as a no-op (don't crash the homepage on a new block type).
- Static-content blocks carry HTML — same sanitise note as CMS pages.

---

## UI/UX

- **Selectors:** compact, keyboard-navigable header dropdowns for channel/currency/language; show the current selection; persist the choice; re-fetch dependent data (catalog/prices) on change.
- **RTL:** honour the locale's `direction` — flip layout for `rtl` locales, don't just translate text.
- **Footer:** build policy links from the CMS pages list, not a hardcoded array, so new pages appear automatically.
- **Homepage:** data-driven from theme blocks; graceful skeleton while loading; tolerant of unknown block types.
- **Loading/caching:** prefetch context on first load; these feeds shouldn't block interactive UI — show sensible defaults while they resolve.
- **a11y:** selectors are proper labelled `<select>`/listbox controls; CMS/theme HTML keeps a sane heading order; carousels are keyboard-operable with pause control.

---

## GraphQL notes

- Collections (`countries`, `countryStates`, `channels`, `currencies`, `locales`, `pages`, `themeCustomizations`) are **cursor-paginated** (`edges`/`node`, `pageInfo`); singles (`country`, `countryState`, `channel`, `currency`, `locale`, `page`, `themeCustomization`) take an id. Select documented fields, one per line.
- `themeCustomizations` accepts a `type` argument to filter blocks.
- All public — storefront key only, no token.

---

## Checklist

- [ ] Country/state dropdowns driven by `countries` + `countries/{id}/states` (or `country-states`); dependent + cached; no-state countries handled.
- [ ] Channel/currency/locale selectors fetched from the API (not hardcoded); choice persisted; catalog re-fetched on change; prices rendered from API `formatted*`.
- [ ] Locale `direction` drives RTL layout.
- [ ] Footer links built from `pages`; each CMS page rendered on its own route; HTML sanitised.
- [ ] Homepage built from `theme-customizations` blocks by `type`; unknown types are no-ops; HTML sanitised.
- [ ] All context feeds cached/prefetched; never block interactive UI.
- [ ] Selectors accessible; carousels keyboard-operable; storefront key always sent.
