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

A merchant follows a procedure with the admin open beside the page, so every
action has to be findable at a glance. When the order matters, write a numbered
list under a heading that names the outcome, one action per step, and end with
the save:

```md
## Allow back orders

1. Go to **Configure >> Catalog >> Inventory**.
2. In the **Product Stock Option** section, switch **Allow Back Orders** on.
3. Set the **Out-of-Stock Threshold**.
4. Click **Save Configuration**.

<ImagePopup src="/images/configure/backorder.png" alt="Product Stock Option settings" />
```

Rules that keep procedures usable:

- **Never chain actions in a sentence.** "Go to Configure, open General, enable
  X and save" is four steps written as one; split it. The same applies to
  "click X, select Y, enter Z", to "At last click Save", and to a paragraph
  that walks through a screen.
- **One action per step**, phrased as an imperative: go to, open, switch on,
  enter, choose, click. A step may end with the visible result ("You are
  redirected to the edit page").
- **The first step is the menu path**, written as **Configure >> Group >>
  Sub-group** or **Catalog >> Products**, exactly as the admin labels it.
- **Plain Markdown numbers**, `1.` `2.` `3.`; a bold `**Step 1:**` label is an
  older style and is not used for new writing.
- **No one-step lists**, and no numbering of things that are not actions. A
  screen's options, a form's fields and a list of prerequisites are bullets.
- **A screenshot belongs after the step it illustrates**, not before, and not
  at the top of the page standing in for all of them. Where the steps continue
  after the image, keep numbering (Markdown restarts the count if a paragraph
  breaks the list, so write the number explicitly, `4.`, and it resumes).

When order does not matter — a set of things a screen lets you do — use a bullet
list with the action bolded, not fake steps:

```md
- **Reorder** — drag a section by its handle to change where it appears.
- **Switch on or off** — use the toggle on the row.
- **Duplicate** or **Delete** — from the row's menu.
```

Before calling a page done, search it for the run-on patterns — "and then",
"then click", "After that", "At last", "Finally click", a comma-separated chain
of verbs — and rewrite every hit.

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

**Every bold label is copied from the language file, not from memory.** Admin
labels live in `packages/Webkul/Admin/src/Resources/lang/en/app.php`, storefront
labels in `packages/Webkul/Shop/src/Resources/lang/en/app.php`; grep the string
before writing it. The audits that found the most defects were label audits —
"Rule Information" sections that do not exist, "Add Slots" buttons that are
hidden for the type being described, "Products with Most Visits" cards that
were never shipped — and every one of them read as confident. Fields are
listed in the order the form shows them, which is the order they appear in the
Blade view, not the order that seems logical.

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

## Navigation order

The sidebar is read top to bottom by someone setting up a store, so it follows
that journey rather than the order pages were written in:

1. Getting started: introduction, the command palette, the admin account.
2. Generative AI: an overview, then one page per feature (text content, product
   images, image search, review translation, checkout message). Configuration
   stays under Configure; the feature pages link to it rather than repeating it.
3. Theme: themes and sections.
4. Store setup: channels, locales, currencies, exchange rates, inventory
   sources, taxes, users, roles, data transfer.
5. Configure, in the admin's own order: an overview, then General (General,
   Content, Design, Exchange Rates, Sitemap, GDPR), Generative AI (Magic AI)
   (the configuration page only), Sales (Shipping Settings, Shipping Methods,
   Payment Methods, Checkout, Order Settings, Invoice Settings, Taxes, RMA, EU
   Withdrawals), Catalog (a nested Products group with one page per section of
   that screen, then Inventory and Rich Snippets), Customer, Email, Search
   Engines, File Management, Cache Management, About.
6. Catalog: categories, attributes, product types.
7. Customers, then Sales (orders, invoices, shipments, refunds, transactions, EU
   withdrawals, returns), then Marketing and CMS.
8. Reporting.
9. Paid extensions, each under its own name, last.

Group labels are the admin's own words in sentence case, one concept per
group, no duplicate entries, and a page moves group when the feature moves in
the admin. Nested groups are for a set of pages that share one screen (the
Configure groups, the product types); do not nest for the sake of it. Every
group, top-level or nested, is expanded by default (`collapsed: false`), and
each level is indented under the one above it by the sidebar styles in
`.vitepress/theme/custom.css`; check both in the built site after changing the
sidebar.

## The marketplace guide

The Multi-Vendor Marketplace guide is a user guide with three readers instead of
one: the store admin who runs the marketplace, the seller who runs a shop in the
**Seller Panel**, and the customer on the storefront. A page that mixes their steps
without saying whose panel they happen in is a defect.

- **Badge every page.** Under the H1, add the role badges for the panels the steps
  happen in (`role--admin`, `role--seller`, `role--customer`, styled in the site's
  `custom.css`). Where a page covers two readers, give each its own `##` section,
  and start each procedure with that panel's menu path: **Marketplace >> Sellers**
  in the admin panel, **Catalog >> Products** in the Seller Panel.
- **The navigation follows who does the work**: getting started (an introduction
  and a quick start for admins and for sellers), Generative AI, sellers, the Seller
  Panel, catalog, inventory, pricing, marketing, orders and fulfilment, payments
  and commission, subscription plans, customers and communication, the storefront,
  reviews and moderation, reporting, then configuration with one page per
  **Configure >> Marketplace** screen.
- **The inventory comes from the package.** The admin menu, seller menu, both
  permission trees and the configuration tree live in the Marketplace package's
  `Config/` directory; account for every screen in them.
- **Document permission names from the ACL files.** When a grid checks a different
  permission key than the ACL defines, don't describe the resulting behaviour as
  intended; report it to the developers instead.
- **Generative AI for sellers is one feature.** Sellers generate product content
  from a description and photos, review it and save it. Don't describe image
  generation, automation or agents for the marketplace.

## Configuration pages

A page under Configure documents one Configuration screen, the tile a merchant
clicks, with its sections in the order the screen shows them. A screen too long
to read as one page, such as **Catalog >> Products**, gets one page per section,
nested in the sidebar under the screen's name.

- **Build the inventory from the running app, not from the old pages.** The
  merged tree in `config('core')` lists every group, screen, section and field
  with its label, type, default, scope and dependency. Compare it with the
  guide screen by screen; a section missing from the guide is a defect even if
  no page ever mentioned it.
- **Open with the path**, **Configure >> Group >> Screen**, as the tile is
  labelled, and number the steps inside each section.
- **Say the scope.** A field with the channel badge is saved per channel, one
  with the language badge per language. Tell the reader to choose the channel
  or language first, and remember that each selector only appears when there
  is more than one to choose from.
- **Explain what appears.** When fields appear only after a switch is turned
  on or an option is chosen, say so in the step: "The other settings appear."
- **Defaults come from the configuration file**, not from whatever the demo
  store currently holds. If the file sets none, don't state one.
- **Check the effect in the code before describing it.** A setting's label and
  info text describe intent; the storefront or admin code that reads it
  describes behaviour, and the two disagree more often than expected.
- **Settings meant for developers**, such as a number generator class, get one
  plain sentence: leave it empty unless a developer has set it up.
- **Use a table** when a section has more than three settings: the bold label,
  then what it does, in screen order.
- **Configuration and feature pages don't repeat each other.** The feature page
  says what the feature does and links to the configuration page; the
  configuration page says how to set it up and links back. Two pages for one
  setting are merged, and the removed URL is redirected.
- **Differences in Bagisto 2.4** go in a short closing section when a screen or
  setting sits elsewhere, is missing, or behaves differently there.

## Versions

One guide covers every supported release. Describe the current admin, which is
**Bagisto 2.5** and is called that ("available from Bagisto 2.5", never "on the
current version of Bagisto"), and add a short "On Bagisto 2.4 …" sentence only
where a setting sits somewhere else or is missing on the supported release.
Never mark a feature as beta.

## AI features

The capability is **Generative AI**; **Magic AI** is the admin's name for it and
stays in parentheses, in the menu path (**Configure >> Magic AI**) and on the
buttons, which are labelled Magic AI. Keep configuration and usage apart: the
Configure page says how to switch things on and connect a provider, the
Generative AI section says what each feature does and how to use it, one page
per feature, each linking back to the configuration it needs. Describe each
feature from the merchant's side: what it writes, draws, translates or
recognises, where the button is, and that nothing is applied until the admin
clicks Apply. Do not call these features agentic and do not promise automation
the store does not perform; the storefront features respond to a shopper's
action or to an order being placed.

## Style

- **Bold** for anything the reader clicks or types: menu paths, button labels,
  field names, values.
- `>>` between menu levels: **Appearance >> Themes**.
- Sentence case in headings — "Creating a section", not "Creating A Section".
- Wrap prose at a readable width; do not reflow a paragraph you did not change,
  or the diff buries the edit.
- No screenshots of text. If it can be typed, type it.
- No "simply", "just", "easily". If it were easy the page would not exist.
