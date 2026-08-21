# Writing for a merchant

## Who is reading

Someone running a store, or setting one up for a client. They have the admin
panel open in another tab. They have never seen the source, do not know what a
package is, and are looking for the one screen that does the thing they came
for.

Everything follows from that:

- **Name what is on screen, in the words that are on screen.** "Go to
  **Appearance >> Themes**" — the same menu labels, the same button captions,
  bolded so they stand out from the prose.
- **Do not name code.** No class names, no table names, no config keys, no
  events, no file paths. If a sentence needs one, it belongs on the developer
  side — see [developer-docs.md](developer-docs.md).
- **Explain the consequence, not the mechanism.** "Nothing goes live until you
  publish" is the merchant's version of a draft column. The reader needs to know
  what happens to their storefront, not which column holds it.
- **Second person, present tense.** "You can" and "the editor shows", not "the
  user may" or "the system will".

## Page shape

Most pages have no frontmatter. They open with an `#` H1 and a short paragraph
saying what the feature is and why it matters, then `##` sections following the
order a merchant meets them.

```md
# Appearance

The appearance of your storefront defines its look and feel, and is a key factor
in the first impression it makes on a visitor.

## Themes

Go to **Appearance >> Themes** to see every theme, grouped so you can tell at a
glance which are ready to use:

- **My Themes** — themes installed on your store.
- **Buy Themes** — themes available from the marketplace.

<ImagePopup src="/images/appearance/themes.png" alt="Themes" />
```

One H1 per page, and it doubles as the page title, so it should match the
sidebar entry closely enough that a reader arriving from the sidebar knows they
landed in the right place.

Add frontmatter only when a page needs something VitePress cannot infer — a
custom layout, or a title different from the H1. Most pages do not, and adding
an empty block to every new page is churn.

## Images go through the site's image component

A merchant-facing site is screenshot-heavy, so it registers a click-to-zoom
component rather than using plain markdown image syntax. A flat `![alt](src)`
cannot be enlarged, which is useless for a screenshot of a dense admin form.

Check what the site registers before writing the first image:

```bash
grep -n "app.component(" .vitepress/theme/index.ts
```

Where that component is `ImagePopup`:

```md
<ImagePopup src="/images/appearance/section-editor.png" alt="Section Editor" />
```

`src` is absolute from `src/public`, so `src/public/images/x/y.png` is
`/images/x/y.png`.

**`alt` describes *this* image.** Copy-pasting the previous image's alt text is
the single most common defect on the merchant side — whole sequences of a dozen
screenshots share one alt. It is what a screen reader announces, so it has to
name what the picture shows.

Capture, clean setup and file naming are in [screenshots.md](screenshots.md).

## Procedures

When the order matters, number the steps and keep one action per step:

```md
**Step 1:** In the editor, click the **+** button beside the section list.

**Step 2:** Choose the section type, give it a name, and save.

<ImagePopup src="/images/appearance/create-section.png" alt="Create Section" />

**Step 3:** The section is added, switched off, and opened for editing.
```

When order does not matter — a set of things a screen lets you do — use a bullet
list with the action bolded, not fake steps:

```md
- **Reorder** — drag a section by its handle to change where it appears.
- **Switch on or off** — use the toggle on the row.
- **Duplicate** or **Delete** — from the row's menu.
```

A screenshot belongs after the step it illustrates, not before, and not at the
top of the page standing in for all of them.

## Fields

For a form, describe the fields in the order they appear, with the label in bold
followed by what it does. Give the constraint the reader cannot guess — an image
size, a limit, a format:

```md
**Title:** The slide title.
**Link:** Where the slide points.
**Image:** The slide image. A resolution of **1920 × 700** is recommended.
```

Skip fields whose label is the whole explanation. A row reading
"**Name:** The name." wastes the reader's attention and pushes the field that
does need explaining further down.

## Behaviour worth calling out

Some things surprise people, and a page that omits them generates support
questions:

- State that is held rather than applied immediately.
- An action that cannot be undone.
- A limit — one footer per channel, one active theme per channel.
- Something that happens automatically as a side effect.

Give each its own short `###` section with a plain-language heading, in the
merchant's terms:

```md
### Nothing goes live until you publish

Every change is held as an **unsaved change** until you publish it.
```

## When a feature moves in the admin panel

The admin panel changes between releases, and the guide has to move with it. A
page for a feature that moved needs all of:

1. The page file moved to the new section folder.
2. Its images moved to the matching `src/public/images/<section>/` folder and
   every image `src` updated.
3. The sidebar entry moved to the new group.
4. The old URL redirected — see [publishing.md](publishing.md).
5. Screenshots recaptured if the screen itself changed, not only its location.

Add a short closing section for readers upgrading, so someone searching for the
old name still lands somewhere useful:

```md
## Upgrading from an earlier version

If you used **Settings >> Themes** before, that screen has moved. Theme
customizations are now sections, and they live under **Appearance**.
```

## Style

- **Bold** for anything the reader clicks or types: menu paths, button labels,
  field names, values.
- `>>` between menu levels: **Appearance >> Themes**.
- Sentence case in headings — "Creating a section", not "Creating A Section".
- Wrap prose at a readable width; do not reflow a paragraph you did not change,
  or the diff buries the edit.
- No screenshots of text. If it can be typed, type it.
- No "simply", "just", "easily". If it were easy the page would not exist.
