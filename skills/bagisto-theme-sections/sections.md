# Section types, schema and media

## Contents

- [The six types](#the-six-types)
- [Which types a theme offers](#which-types-a-theme-offers)
- [The field schema](#the-field-schema)
- [Field kinds](#field-kinds)
- [Adding a type](#adding-a-type)
- [Sanitising](#sanitising)
- [Where a type is rendered](#where-a-type-is-rendered)
- [Full page cache](#full-page-cache)

## The six types

`SectionTypeEnum` names the core types; each case maps to a class under
`Webkul\Theme\Sections` extending `SectionType`, which owns the type's code,
title, icon, fields and behaviour:

| Type | Renders | Flags |
|---|---|---|
| `image_carousel` | A slider of linked images | |
| `product_carousel` | A product strip, driven by filters | |
| `category_carousel` | A category strip, driven by filters | |
| `static_content` | Author-supplied HTML and CSS | `sanitize()` |
| `services_content` | The service promises drawn by the layout | `$layout` |
| `footer_links` | The footer's link columns — **one per channel** | `$singleton`, `$pinned`, `$layout` |

A section belongs to one **theme code** and one **channel**, so the same theme
customised on two channels is two independent sets of sections.

`Section::TYPES` and the `Section::*` constants remain only as deprecated aliases.

## Which types a theme offers

`config('themes.shop.{code}.customize.sections')` lists the types a theme offers **in tile
order**. The convention, used in `config/themes.php` and `UPGRADE.md`, is one form
per kind: a **core type as its `SectionTypeEnum` case**, a **theme's own type as its
`SectionType` class**. (The resolver also accepts a core value string such as
`'image_carousel'`, but do not document or suggest it.) Absent, the theme offers
every core type in enum order; the `default` theme lists all six as enum cases.
`SectionSchema::types($code)` reads it, and everything theme-aware goes through
it: create validation, the editor tiles (sent already ordered — Vue only filters),
the singleton guard.

- **First declaration of a code wins**, position and class, so
  `[Hero::class, SectionTypeEnum::PRODUCT_CAROUSEL, ...SectionTypeEnum::cases()]`
  leads with two types and fills in the rest in enum order without duplicates.
- **An invalid entry is reported and skipped**, never thrown, so the editor stays up.
- Tile order is not section order: placed sections keep their `sort_order`.

A stored section resolves its type with
`$section->getTypeInstance()`, which falls back to the core type of that code so
stale core sections still sanitise and edit.

## The field schema

The editor draws no per-type form. `SectionType::getFields()` returns a field
list and the editor renders it generically, which is why adding a type needs no
view. `SectionSchema::for($type, $themeCode)` is the entry point.

| Type | Fields |
|---|---|
| `image_carousel` | `images` (repeater) |
| `product_carousel` | `title` (text), `filters` (filters — extend via `filterKeys()`) |
| `category_carousel` | `filters` (filters — extend via `filterKeys()`) |
| `footer_links` | `columns` (repeater of `links` repeaters, optional `max`) |
| `static_content` | `html`, `css` (code) |
| `services_content` | `services` (repeater) |

A type may edit a different shape from the one it stores:
`prepareForEditor()` shapes stored options for the `fields` endpoint and
`prepareForStorage()` shapes the posted draft back. The footer edits a list of
columns but stores `column_1..N`, which the storefront and theme footers read.

The controller's `fields` endpoint returns the schema together with the values
to show — **the draft when one is pending, the published options otherwise** —
so reopening a section restores the staged edit rather than the live value.

## Field kinds

| Kind | Control | Extra keys |
|---|---|---|
| `text`, `number`, `textarea` | A plain input, labelled | — |
| `image` | An upload through the section's media endpoint, stored as its path | — |
| `code` | A CodeMirror editor | `language` |
| `repeater` | A repeating, draggable group with an add button | `fields`, `add_label`, `max` |
| `filters` | Key/value filter rows, keys drawn from the type | `keys` (`value`, `label`, `options`, `multiple`) |

The controls are schema-driven and **carry no `name` attribute** — they bind
with `v-model`. Anything addressing them (a test, an override) has to go through
the label above the control. See the `bagisto-playwright-testing` skill.

Edits are debounced and posted to the draft endpoint; there is no explicit save
for content, only Publish and Discard.

## Adding a type

For a theme's own type — no core file changes:

1. A class extending `SectionType` (or a core type) with `$code`, `$title`,
   `$icon`, `getFields()` and any flags. Only `$code` is required.
2. List it under the theme's `customize.sections` in `config/themes.php`, where its position
   is its tile position.
3. Render it from the theme's own home or layout views, tolerating empty options,
   and mark it with `data-section-id` / `data-section-name` while previewing.
4. Translations in the theme's own namespace.

`UPGRADE.md` → *Adding sections to a theme* walks through every variant with
code: reordering core types, a new type, extending a core type under a new code,
replacing one under its own code, layout, singleton and pinned types, sanitising,
and editing a different shape from the stored one.

For a core type: add the enum case and its `getClassName()` arm, the class, the
storefront partial, and the labels in all 22 locales.

`$layout` makes FPC clear every page on change; `$singleton` is guarded
server-side by the controller as well as withdrawn from the tiles.

## Sanitising

`static_content` is author-supplied markup and is the one core type that must be
cleaned. The repository's `sanitizeOptions()` hands the options to the type's
`sanitize()` — `StaticContent` runs Purify over the HTML (`sanitizeHtml()`) and
`sanitizeCss()` over the CSS — on **both** the draft and the publish path, so a
preview never renders anything the storefront would not.

Two things to know:

- **Purify strips `id` attributes** by default. CSS or JavaScript keyed on an
  id will silently stop matching — and a test that greps for the id will report
  a false failure.
- **`StaticContent::sanitize()` uses `array_key_exists` guards**, so it never
  invents a key that was not submitted — a type overriding `sanitize()` must do the same. Adding a key on the way through would create empty
  fields on every save.

Any new write path for section content must go through it.

## Where a type is rendered

- **Home page** — `product_carousel`, `category_carousel`, `image_carousel`,
  `static_content`, drawn in `sort_order`. In the preview each is wrapped in the
  section data attributes unless its type `rendersInLayout()`.
- **Layout, every page** — `footer_links` and `services_content`, looked up with
  `findOneOfType()` / `findAllOfType()`, which serve drafts while previewing.

A layout partial must tolerate an **empty** section. A `services_content`
section with no services once broke every storefront page; the partial now skips
a section whose options are empty. Any new partial needs the same guard, because
a section is created before it has content.

## Full page cache

FPC listens to `section.create.after`, `section.update.after` and
`section.delete.before`, and asks the section's type:

- `rendersInLayout()` true clears the **whole** cache — it appears on every page.
- Anything else clears the **home page** only.

A staged change is not published, so it does not need to clear anything; the
publish does. If a new action changes what the storefront renders, it must fire
the matching event or the cache will serve the old page.
