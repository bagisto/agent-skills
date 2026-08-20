# Section types, schema and media

## Contents

- [The six types](#the-six-types)
- [The field schema](#the-field-schema)
- [Field kinds](#field-kinds)
- [Adding a type](#adding-a-type)
- [Sanitising](#sanitising)
- [Where a type is rendered](#where-a-type-is-rendered)
- [Full page cache](#full-page-cache)

## The six types

`Section::TYPES` is the authoritative list, each a class constant:

| Type | Renders |
|---|---|
| `image_carousel` | A slider of linked images |
| `product_carousel` | A product strip, driven by filters |
| `category_carousel` | A category strip, driven by filters |
| `static_content` | Author-supplied HTML and CSS |
| `services_content` | The service promises drawn by the layout |
| `footer_links` | The footer's link columns — **one per channel** |

A section belongs to one **theme code** and one **channel**, so the same theme
customised on two channels is two independent sets of sections.

## The field schema

The editor draws no per-type form. It asks `SectionSchema::for($type)` for a
field list and renders it generically, which is why adding a type needs no view:

| Type | Fields |
|---|---|
| `image_carousel` | `images` (repeater) |
| `product_carousel` | `title` (text), `filters` (filters) |
| `category_carousel` | `filters` (filters) |
| `footer_links` | `column_1`, `column_2` (repeaters) |
| `static_content` | `html`, `css` (code) |
| `services_content` | `services` (repeater) |

The controller's `fields` endpoint returns the schema together with the values
to show — **the draft when one is pending, the published options otherwise** —
so reopening a section restores the staged edit rather than the live value.

## Field kinds

| Kind | Control |
|---|---|
| `text`, `number`, `textarea` | A plain input, labelled |
| `code` | A CodeMirror editor |
| `repeater` | A repeating group with an add button |
| `filters` | Key/value filter rows, keys drawn from the type |

The controls are schema-driven and **carry no `name` attribute** — they bind
with `v-model`. Anything addressing them (a test, an override) has to go through
the label above the control. See the `bagisto-playwright-testing` skill.

Edits are debounced and posted to the draft endpoint; there is no explicit save
for content, only Publish and Discard.

## Adding a type

1. Add the constant to `Section::TYPES`.
2. Add its field list to `SectionSchema`.
3. Add the storefront partial that renders it, and call it from the layout or
   the home page.
4. Add the label to all 22 locales, plus any field labels.
5. If it should be drawn on every page rather than the home page, add it to
   `FPC\Listeners\Section::LAYOUT_TYPES` — otherwise editing it will not clear
   the pages it appears on.
6. If it should be a singleton like `footer_links`, guard it **server-side** in
   the controller as well as hiding the tile in the editor.

The editor needs no change: it offers whatever `SectionSchema` describes.

## Sanitising

`static_content` is author-supplied markup and is the one type that must be
cleaned. `sanitizeOptions()` runs Purify over the HTML and `sanitizeStaticCss()`
over the CSS, and it runs on **both** the draft and the publish path, so a
preview never renders anything the storefront would not.

Two things to know:

- **Purify strips `id` attributes** by default. CSS or JavaScript keyed on an
  id will silently stop matching — and a test that greps for the id will report
  a false failure.
- **`sanitizeOptions()` uses `array_key_exists` guards**, so it never invents a
  key that was not submitted. Adding a key on the way through would create empty
  fields on every save.

Any new write path for section content must go through it.

## Where a type is rendered

- **Home page** — `product_carousel`, `category_carousel`, `image_carousel`,
  `static_content`, drawn in `sort_order`.
- **Layout, every page** — `footer_links` and `services_content`.

A layout partial must tolerate an **empty** section. A `services_content`
section with no services once broke every storefront page; the partial now skips
a section whose options are empty. Any new partial needs the same guard, because
a section is created before it has content.

## Full page cache

FPC listens to `section.create.after`, `section.update.after` and
`section.delete.before`, and chooses what to clear from the type:

```php
public const LAYOUT_TYPES = ['footer_links', 'services_content'];
```

- A layout type clears the **whole** cache — it appears on every page.
- Anything else clears the **home page** only.

A staged change is not published, so it does not need to clear anything; the
publish does. If a new action changes what the storefront renders, it must fire
the matching event or the cache will serve the old page.
