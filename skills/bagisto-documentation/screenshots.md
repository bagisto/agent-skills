# Screenshots

A screenshot is a claim about what the reader will see. It has to be captured
from a store that looks like a fresh install, not from the machine you happen to
be developing on.

This applies to any documentation site that carries images, though it is the
merchant-facing guides that live or die by them.

## Capture with Playwright, not by hand

A hand-taken screenshot carries whatever the window happened to contain: a
different viewport each time, a stray tooltip, the developer's own browser
chrome. Drive it with Playwright instead, so every image in a sequence is the
same size and the same state, and so it can be recaptured identically when the
UI changes.

```js
import { chromium } from '@playwright/test';

const base = process.env.DEV_URL;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });

await page.goto(`${base}/admin/login`);
await page.fill('input[name="email"]', 'admin@example.com');
await page.fill('input[name="password"]', 'admin123');
await page.press('input[name="password"]', 'Enter');
await page.waitForURL('**/admin/dashboard');

await page.goto(`${base}/admin/appearance/themes`);

await page.mouse.move(1200, 400);
await page.waitForTimeout(2400);

await page.screenshot({ path: process.env.SHOT });

await browser.close();
```

`admin@example.com` / `admin123` are what `AdminsTableSeeder` writes, so they
work on any freshly seeded store.

Four details in that script earn their place:

- **A fixed 1600 × 1100 viewport.** Every image on a page should be the same
  width, or the page becomes a ragged column of different-sized pictures. 1600
  is wide enough that the admin sidebar and the content area both fit without
  the responsive layout collapsing.
- **`page.mouse.move(...)` away from the content.** The pointer starts at (0,0),
  which sits over the sidebar and leaves a hover highlight on whatever menu item
  is there. Park it somewhere inert before the shot.
- **A wait before capturing.** Admin pages animate in and load their DataGrid
  over XHR. Capturing immediately gets a shimmer placeholder. Prefer waiting on
  the thing you are photographing — `await page.getByText('My Themes').waitFor()`
  — and fall back to a timeout only when there is nothing stable to wait on.
- **Headless.** A headed run picks up the host's font rendering and window
  decorations, so the same script produces a different image on another machine.

Run it from the scratch directory, not from inside the docs repository, and copy
the finished image in.

## The store must be clean

| Check | Why | How |
|---|---|---|
| **Debug bar off** | The Laravel debug bar pins a black toolbar across the bottom of every admin page. It is in a large share of the older screenshots and it dates them instantly. | `DEBUGBAR_ENABLED=false` in `.env`, then `php artisan optimize:clear` |
| **Seeded data only** | "test test", "asdf", `Product 12345` and a customer called "aaa" all read as a broken product to a merchant evaluating Bagisto. | Capture on a fresh `php artisan bagisto:install`, or a store seeded with the sample data |
| **No personal data** | Real names, real email addresses, real order numbers and anything from a client's store must never ship. | Use the seeded customers, or names that are obviously fictional |
| **Light mode** | Screenshots are light-mode throughout; one dark-mode image in a sequence looks like a rendering fault. | The admin default is light — do not toggle it |
| **English locale** | The pages are written in English and their screenshots must match the words in the prose. | Leave the admin locale at English |
| **Default theme, default channel** | A customised storefront is not what the reader will see. | Do not capture from a store you have been theming |

### Seed the data through the screens

A feature with no data photographs as an empty grid, which tells the reader nothing.
When the store is empty, create the data the pages need through the real screens
before capturing: register sellers and customers on the storefront forms, approve them
in the admin, list products in the Seller Panel, place orders at checkout. Doing it
through the UI also checks every workflow the page describes. Use obviously fictional
names and `example.com` addresses, and keep a record of every account you create.

- **No placeholder data.** Lorem ipsum, random UUID SKUs and "test" names in any part
  of the picture, background included, are reason to recapture.
- **Never reuse a screenshot from another store**, even of the same feature. If a state
  can't be reached on the store you are documenting, for example because it needs a paid
  AI provider, describe that state in text and leave the picture out.
- **Run commands inside the app's container as the web server's user**
  (`docker exec -u <user> …`). A command run as root leaves root-owned cache files, and
  the store then fails with errors that look like product bugs.
- **Sign in fresh before every capture run.** Saved sessions expire after a couple of
  hours, and a script that follows the redirect saves the sign-in page over a good
  screenshot. Refresh the saved logins first, and stop a group as soon as a page lands
  on a login URL.
- **Pick select options the way a person does.** Some forms load the next field when a
  select changes, such as return reasons, booking slots or a report's period. Setting
  the value from a script doesn't trigger that. Focus the select and use the arrow keys.
- **Produce the state the page describes.** Check the code for when a screen appears
  before you try to photograph it. For example, an import that validates cleanly starts
  on its own, so its "ready to start" screen only appears when some rows fail.

`DEBUGBAR_ENABLED` is the surgical switch: the package reads
`env('DEBUGBAR_ENABLED')` and falls back to `app.debug` only when it is unset,
so setting it to `false` hides the bar while leaving `APP_DEBUG=true` for your
own work.

## Framing

- **Photograph the thing, not the whole browser.** For a form, a modal or a
  single card, capture that element rather than the full page:
  `await page.locator('.modal').screenshot({ path: ... })`. A full-page shot of
  a screen whose subject occupies a sixth of it makes the reader hunt.
- **A full-page shot is right when position is the point** — where a menu item
  sits, what the dashboard looks like as a whole.
- **Never crop to hide something.** If the shot contains something that should
  not ship, fix the store and capture again.
- **Do not annotate.** No red arrows, no circles, no numbered callouts baked
  into the image. They cannot be translated, they cannot be updated without the
  original, and the prose should be carrying that weight anyway.
- **A configuration screen: its header and the sections the steps cover.** Crop
  to the screen's title row and channel and language selectors, plus the
  section rows the page describes, at the width of the content area, so every
  configuration image in the guide has the same width. Turn on the switch a
  field depends on so the field is visible in the picture.
- **Don't save settings on a shared store to take a picture.** Change fields
  for the capture and leave without saving. If a storefront result only appears
  after saving, describe it in the text rather than changing the store.
- **No secrets and no pre-release labels.** Put obvious placeholders such as
  `your-api-key` in key fields. Don't ship a screenshot of a third-party console
  that shows a real key, or of a screen that shows a beta or development
  version string; describe that screen in text instead.
- **Verify every old image before keeping it.** An image is current only if it
  matches the admin of the release being documented — the header, the field
  labels and badges, the buttons. An old header or an annotation is reason
  enough to replace it.

## Naming

Kebab-case, `.png`, in `src/public/images/<section>/`, where `<section>` is the
folder the page lives in.

**A standalone image is named for what it shows:**

```
src/public/images/appearance/section-editor.png
src/public/images/appearance/create-section.png
```

**An image in a numbered walkthrough is named `<n>-<topic>.png`, and `n` is the
step number:**

```
src/public/images/b2b-ecommerce-platform/1-requisition.png
src/public/images/b2b-ecommerce-platform/2-requisition.png
src/public/images/b2b-ecommerce-platform/3-requisition.png
```

The number and the step have to stay in lockstep. If you insert a screenshot
between steps 2 and 3, renumber the rest of the sequence and update every
`ImagePopup` on the page — do not name it `2a-requisition.png` or `3-new.png`.
The number is the only thing telling a reader which picture goes with which
instruction.

Never `Screenshot 2026-08-21 at 14.32.11.png`, `image (1).png`, `new.png`, or
anything with a space in it. Two files in this repository still carry spaces in
their names and both had to be worked around when they were referenced.

## Referencing

How an image is written into a page depends on the site: a screenshot-heavy
guide registers a click-to-zoom component, while a mostly-text site uses plain
markdown. Check before writing the first one:

```bash
grep -n "app.component(" .vitepress/theme/index.ts
```

Either way the path is absolute from `src/public`, so
`src/public/images/x/y.png` is `/images/x/y.png`, and the alt text names what
*this* image shows — not the page title, and not whatever the previous image's
alt happened to be. See [user-guide.md](user-guide.md) for the component form.

## Before you call it done

```bash
npm run docs:build
```

Then check the things the build cannot:

- Every new image is referenced by a page, and every referenced image exists.
- The image matches the prose beside it, button labels included.
- Every image in the sequence is the same width.
- The debug bar is in none of them.

A quick sweep for references that point at nothing. It catches both the
component form and plain markdown, so it works on any of the sites:

```bash
grep -rhoE '(src="|\]\()/images/[^")]+' src --include=*.md \
  | sed 's/^src="//;s/^](//' | sort -u \
  | while read -r p; do [ -f "src/public$p" ] || echo "missing: $p"; done
```
