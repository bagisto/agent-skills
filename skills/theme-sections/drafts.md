# The staging model

## Contents

- [What is held, and where](#what-is-held-and-where)
- [Nulling a draft that matches live](#nulling-a-draft-that-matches-live)
- [Ordering](#ordering)
- [Publishing and discarding](#publishing-and-discarding)
- [Reading: live versus drafted](#reading-live-versus-drafted)
- [The preview](#the-preview)
- [Media](#media)

## What is held, and where

Three columns, one per kind of change:

| Change | Column | Table |
|---|---|---|
| Content | `draft_options` | `theme_section_translations` (per locale) |
| On/off | `draft_status` | `theme_sections` |
| Order | `draft_sort_order` | `theme_sections` |

Each has a repository method, and none of them touch the live value:

```php
$sectionRepository->saveDraft($id, $locale, $options);   // content
$sectionRepository->saveStatusDraft($id, $status);       // on/off
$sectionRepository->saveOrderDraft($sectionIds);         // order
```

`hasDraft($section)` is true when any of the three is set — `draft_status` is
not null, `draft_sort_order` is not null, or any translation has
`draft_options`. It is what the editor's unsaved count and the per-row dot read,
so a new kind of staged change must be visible to it or it will not be counted.

A newly created section is staged too: it is written with `status = 0` and
`draft_status = true`, so it appears in the preview and counts as unsaved, but
does not reach the storefront until published. Duplicating a section behaves the
same way.

## Nulling a draft that matches live

A draft column is set to **null** when the new value equals the live one:

```php
$section->draft_status = $status === (bool) $section->status ? null : $status;
```

So toggling a section off and back on leaves nothing staged, rather than a
pending change that would publish to the value already in place. Any new staged
field should do the same, or the unsaved count drifts upward and never returns
to zero.

## Ordering

Order is the subtle one. The editor posts the full list of ids in their new
order, and positions are `1..N`. The stored `sort_order` values are **not**
guaranteed to be that sequence — duplicating and deleting leave gaps.

Comparing a position against a gapped stored number reports almost every section
as moved. `saveOrderDraft()` therefore calls `closeOrderGaps()` first,
renumbering the sections `1..N` in the order they are already in — which does
not change what anyone sees — and only then compares:

```php
$sections = $this->findWhereIn('id', $sectionIds)->keyBy('id');

$this->closeOrderGaps($sections);

foreach (array_values($sectionIds) as $position => $id) {
    $order = $position + 1;

    $section->draft_sort_order = $order === (int) $section->sort_order ? null : $order;
}
```

Two consequences:

- **The gap-closing is a live write** — the one thing in the reorder path that
  does not wait for publish. It is safe because renumbering preserves the exact
  sequence, so nothing user-visible changes.
- **Moving one section past its neighbour is two changes, not a whole list.**
  Dragging further genuinely moves everything in between, so a larger count is
  the list actually changing.

## Publishing and discarding

```php
$sectionRepository->publishDraft($id);   // promote all three, then purge media
$sectionRepository->discardDraft($id);   // clear all three, then purge media
```

`publishDraft()` promotes every locale's `draft_options`, not just the one being
edited, then `draft_status` and `draft_sort_order`, then purges media the
published options no longer reference. `discardDraft()` clears the same three
and purges the same way, so an image uploaded into an abandoned draft does not
linger.

The editor publishes either the open section or every section holding a draft;
both go through the same method per section.

## Reading: live versus drafted

Two private methods back every read:

| Method | Returns |
|---|---|
| `live($criteria)` | Published rows, ordered by `sort_order` |
| `drafted($criteria, $locale)` | Rows with drafts resolved over them |

And three public entry points:

| Method | Used by |
|---|---|
| `getRenderable($channelId, $themeCode)` | The storefront |
| `findAllOfType(...)` / `findOneOfType(...)` | Layout partials — branches on `isPreviewing()` |
| `getDraftedForPreview(...)` | The preview, always drafted |

`getDraftedForPreview()` is **unconditional** — it does not consult the
previewing flag. That separation is deliberate: a method that branches on a
request flag will silently serve live data when called outside a preview, which
is the bug that hides longest. Call the one that matches your context.

## The preview

The `appearance-preview` route renders the storefront from drafts. Two guards
hold it:

- **Authorization** — `abort_unless(bouncer()->hasPermission('appearance.sections'), 403)`.
  A logged-in admin without the permission is refused, as is a guest.
- **The flag** — `SectionRepository::PREVIEWING` is set on the request's
  *internal attribute bag*, not read from the query string, so no visitor can
  ask a storefront URL to render unpublished content.

The editor frames the preview at the chosen device width and reloads it after
each staged change.

## Media

Images live under `themes/{theme_code}/sections/{id}/`.

- `purgeUnreferencedMedia()` runs after every publish and discard, deleting
  files whose basename appears in neither `options` nor `draft_options`. The
  basename match is what protects an image embedded in `static_content` HTML,
  where the file is referenced inside markup rather than as its own field.
- **Deleting a section removes its directory via `SectionObserver::deleted()`**,
  not in the controller — so any deletion path cleans up, including a cascade.
