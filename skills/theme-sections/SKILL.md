---
name: theme-sections
description: Use when working on the Bagisto Appearance area — theme sections, the section editor and its storefront preview, draft and publish behaviour, section media, or the theme gallery. Trigger phrases include "section", "theme section", "appearance", "preview", "draft", "publish", "unsaved changes", "storefront layout", "theme gallery", "customize theme".
requires: coding-standards
license: MIT
---

# Theme Sections

`packages/Webkul/Theme` owns the **Appearance** area: the theme gallery, and the
sections a theme's storefront is built from. Sections replaced the old
`settings/themes` CRUD — the routes are gone, and a section is now edited beside
a live preview rather than on a form of its own.

## Reference files

| File | Load when |
|---|---|
| [drafts.md](drafts.md) | The staging model — what is held, what publishing does, the preview |
| [sections.md](sections.md) | Section types, the field schema, media, and the rules per type |

## Where things live

| Path | What |
|---|---|
| `admin/appearance/themes` | The gallery — installed themes and ones on offer |
| `admin/appearance/themes/{code}/sections` | The editor for one theme, on one channel |
| `appearance-preview` (shop) | The storefront rendered from drafts, framed in the editor |

`ThemeCatalog` supplies the gallery; `SectionSchema` supplies the field schema
the editor renders per type; `SectionRepository` owns every read and write.

## Nothing goes live until it is published

This is the rule the whole area is built on. **Every** change is staged —
editing content, toggling a section on or off, and dragging it to a new
position. Each is held on the row and applied only when the operator publishes:

| Change | Held in |
|---|---|
| Content, per locale | `theme_section_translations.draft_options` |
| On/off | `theme_sections.draft_status` |
| Order | `theme_sections.draft_sort_order` |

A draft column is **nulled when it would equal the live value**, so toggling a
section off and back on leaves nothing staged rather than an empty pending
change. `hasDraft()` is true when any of the three is set, and that is what the
editor's unsaved-changes count and per-row dot read.

`publishDraft()` promotes all three and then purges media the published options
no longer reference; `discardDraft()` clears all three and purges the same way.

## Non-negotiables

- **The storefront reads live values, the preview reads drafts.** The switch is
  `SectionRepository::PREVIEWING`, set in the request's *internal attribute bag*
  — never from a query parameter, or a visitor could ask a storefront page for
  unpublished content. Use `getRenderable()` for the storefront and
  `getDraftedForPreview()` for the preview; do not branch on the flag yourself.
- **The preview is admin-only.** `appearance-preview` aborts unless
  `bouncer()->hasPermission('appearance.sections')` — an authenticated admin
  without that permission is not enough.
- **Sanitise on the way in.** `static_content` HTML and CSS pass through Purify
  and `sanitizeStaticCss()` in the repository, on both the draft and the publish
  path. A new write path must go through `sanitizeOptions()`.
- **One footer per channel.** `footer_links` is a singleton, guarded server-side
  in the controller — not only by hiding the type in the UI.
- **Clear the page cache on every change.** FPC listens to `section.create.after`,
  `section.update.after` and `section.delete.before`; `footer_links` and
  `services_content` are drawn by the layout on every page, so those clear the
  whole cache rather than just the home page.
- **Fire before and after events.** Every action dispatches a pair —
  `section.create.*`, `section.update.*`, `section.delete.*`,
  `section.draft.save.*`, `section.draft.discard.*`, `section.media.upload.*`,
  `section.reorder.*`. A new action needs both, or FPC and third-party listeners
  miss it.
- **Guard against a section deleted in another tab.** Every action resolves
  through `sectionOrFail()` and answers with a plain "no longer exists" rather
  than a 500.
- **A section's media directory is removed by `SectionObserver`** on delete, not
  by the controller.

**REQUIRED SUB-SKILL:** Use change-verification before calling any change done.
