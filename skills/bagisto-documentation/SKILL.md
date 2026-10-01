---
name: bagisto-documentation
description: Use when writing or updating any Bagisto documentation site — the developer documentation, the merchant user guide, or any other Bagisto docs repository — covering page content, code samples, screenshots, the sidebar, image naming, and moving or deleting pages. Trigger phrases include "docs", "documentation", "user guide", "developer documentation", "dev docs", "merchant documentation", "marketplace docs", "document this", "update the docs", "add a doc page", "screenshot", "ImagePopup", "redirect a doc page".
requires: bagisto-coding-standards
license: MIT
---

# Bagisto Documentation

Bagisto's documentation lives in **separate repositories from the codebase**,
one per audience. They are all VitePress sites built the same way, so the
mechanics in this skill apply to every one of them — the developer
documentation, the merchant user guide, and any guide added later.

## Step 1: decide who the reader is

Everything else follows from this, so settle it before writing a line. **Judge
by audience, not by which repository you happen to have open** — a repository
can hold a page aimed at either reader, and getting this wrong produces a page
that is technically accurate and useless to whoever arrives.

| Ask | If yes | Load |
|---|---|---|
| Will the reader **write code** against Bagisto — a package, a theme, an integration, an API client? | Developer documentation | [developer-docs.md](developer-docs.md) |
| Will the reader **operate a store** from the admin panel, without touching code? | User guide | [user-guide.md](user-guide.md) |

If a page seems to need both, it is two pages. A merchant reading about a class
name skips it; a developer reading a click path stops trusting the page. Split
by audience and link across.

When a new documentation repository appears — a marketplace guide, a
self-hosting guide — it is one of these two readers under a new name. Run the
same test and use the same reference.

## Step 2: find the repository, do not guess it

Each site is a **separate repository, not a folder inside the Bagisto app**, so
locate it before editing anything:

```bash
find . ~ -maxdepth 6 -type d -path '*/src' -path '*doc*' 2>/dev/null | head
```

If it is not cloned, ask the user for the path or to clone it. **Never invent a
location** and never write a page into the Bagisto app by mistake — the app has
no `src/` docs tree, so a page created there is silently lost.

## Read the neighbours before writing

Open two or three existing pages in the section you are adding to and match
their depth, heading rhythm and tone. A page that reads differently from its
neighbours is a defect even when every fact in it is right.

Check for duplication at the same time: if the topic is already half-covered
somewhere, **extend that page or cross-link to it** rather than forking a second
source of truth. Two pages that partly answer the same question age into two
pages that contradict each other.

## Reference files

| File | Load when |
|---|---|
| [developer-docs.md](developer-docs.md) | Writing for a reader who writes code — voice, structure, code samples |
| [user-guide.md](user-guide.md) | Writing for a reader who runs a store — voice, page shape, steps |
| [screenshots.md](screenshots.md) | A page needs an image — capture, clean setup, naming |
| [publishing.md](publishing.md) | Adding, moving or deleting a page — sidebar, redirects, verification |

## What every site has in common

```
<docs-repo>/
├── src/                       # srcDir — every page
│   ├── <section>/*.md          # one folder per sidebar group
│   ├── index.md
│   └── public/
│       ├── images/<section>/   # per-section image folders
│       ├── llms.txt            # hand-maintained
│       └── llms-full.txt       # hand-maintained
└── .vitepress/
    ├── config.mts              # sidebar, nav, build hooks
    ├── _redirects.ts           # legacy URL map
    └── theme/                  # site-specific Vue components
```

```bash
npm run docs:dev      # local preview
npm run docs:build    # the gate — always run before calling a change done
```

**Learn the site rather than assuming it.** The sites differ in ways that matter
and that change over time, so check rather than recall:

```bash
grep -n "app.component(" .vitepress/theme/index.ts        # custom components, e.g. an image viewer
grep -ohE "'/[0-9][^/]*" .vitepress/_redirects.ts | tr -d "'" | sort -u   # legacy version prefixes
```

The second one matters most: a page that moves needs its redirect repointed
under **every** prefix that site carries, and the count is not the same between
repositories.

## Non-negotiables

- **Write for one reader.** The audience decided in step 1 governs vocabulary,
  what you explain and what you assume. This is the rule that makes a docs page
  good or useless.
- **A published URL never breaks.** Every way a page's URL can change — renaming
  the file, moving it to another section, changing its slug, splitting it in
  two, deleting it — needs an entry in `.vitepress/_redirects.ts` pointing the
  old URL at the content's new home, *and* every existing redirect that aimed at
  the old URL repointed. Nobody updates their links for you. See
  [publishing.md](publishing.md).
- **Never delete a page that is holding a URL open** unless a redirect covers
  that URL first. Some pages exist only to keep a legacy path resolving; they
  look like clutter and are load-bearing.
- **The sidebar is the only navigation.** A page absent from the `sidebar` array
  in `.vitepress/config.mts` is reachable only by typing its URL. Add the entry
  in the same change as the page.
- **Every filename is kebab-case.** Lowercase, hyphen-separated, no spaces, no
  camelCase, no underscores — for pages and images alike. Older files predate
  the rule; match the rule, not the neighbours, and do not rename unrelated
  files while you are there.
- **Inspect the implementation before the existing page.** The page you are
  updating may be describing a feature that has since moved, been renamed or
  been removed. Start from the code, the config files, the language files and
  the running admin; treat the old prose as a hypothesis, not a source.
- **Verify claims against the codebase, not memory.** A confidently wrong
  sentence is worse than no page, because it is believed. Every command,
  path, config key, class, method, route, label and behaviour on a page has to
  come from a file read or a command run in this session. Open the file, run
  the command, check the string.
- **Code samples pass Pint.** A PHP sample is formatted exactly as the
  project's `pint.json` (the `laravel` preset) formats it — single spaces
  around `=>`, trailing commas, sorted imports, no aligned columns — and reads
  like production Bagisto code. Run Pint on extracted samples rather than
  judging by eye; the procedure is in [developer-docs.md](developer-docs.md).
- **Sequential actions are numbered steps.** Wherever a reader must do several
  things in order, write a numbered list with one action per step under a
  heading that names the outcome. A sentence that chains "go to X, click Y,
  enter Z and save" is a defect on the merchant side and a smell on the
  developer side. Bullets are for options, properties and prerequisites, where
  order does not matter.
- **One documentation set across releases.** No per-version page trees, no
  "2.5 beta" labels, and no "current development version" wording: the current
  release is called **Bagisto 2.5**. Name a release only where behaviour or
  availability differs, in the same paragraph as the current behaviour, so the
  page is still right after the next release. See the Versions section in
  [developer-docs.md](developer-docs.md).
- **Generative AI is the term, Magic AI is the name.** Pages and headings say
  "Generative AI (Magic AI)"; "Magic AI" alone is kept for the admin's own
  labels and the package. "Agentic" is reserved for features where an agent
  acts (WebMCP, agent skills). See the AI sections of both reference files.
- **The user guide's navigation follows the merchant's journey**: getting
  started, the headline capabilities (generative AI, then theme), store setup,
  configuration, catalog, customers, sales, marketing, content, reporting, then
  paid extensions. Inside Configure, the groups and their order are the admin's
  own Configuration screen. Reorder it when a page lands in the wrong group. The
  developer documentation's navigation is organised by extension mechanism and
  is **not** reorganised unless the user asks for it.
- **The marketplace guide has three readers.** Badge every page with the panels its
  steps happen in (admin, Seller Panel, storefront), seed realistic data through the
  real screens before capturing, and follow its navigation in the marketplace section
  of [user-guide.md](user-guide.md).
- **Configuration docs start from the configuration tree, not from the old
  pages.** Dump the merged tree the admin renders (`config('core')` in the
  running app) and account for every group, screen and section in it:
  documented, merged into another page, or deliberately left out. See the
  Configuration pages section of [user-guide.md](user-guide.md).
- **AI terminology is earned by the implementation.** "Generative AI" is for
  features that produce content (Magic AI's text, images, translations,
  keywords). "Agentic AI" is for features where an AI agent performs actions
  through tools (WebMCP's storefront tools, coding agents using the skills).
  "Agentic commerce" names the direction the two add up to. Position the
  capabilities plainly on overview pages, keep technical pages technical, and
  never claim autonomy the code does not have: Magic AI applies nothing without
  an admin, and WebMCP tools end on an ordinary page with the shopper in charge.
- **Finish with an independent audit.** After editing, verify the result as a
  reviewer who did not write it: every claim against the code, every sample
  through Pint, every link and image resolved, the sidebar and `llms.txt`
  consistent, then the build. A change that has only been written has not been
  checked.
- **`llms.txt` and `llms-full.txt` are written by hand.** Nothing generates
  them. Adding, moving or deleting a page means editing them too.
- **The build is the gate.** `npm run docs:build` reports each redirect it
  writes. A change that has not been built has not been checked.

## Common mistakes

- **Mixing the two audiences on one page** — the failure this skill exists to
  prevent. Click paths in developer docs, class names in the user guide.
- **Documenting the intended design instead of the shipped behaviour.** When a
  page and the code disagree, the code is right.
- **A stub page left behind after a move.** A page whose whole body is "this
  moved" stays in the sidebar and ranks in search. Redirect it, then delete it.
- **A rename shipped without a redirect.** Fixing a typo in a filename feels
  like tidying rather than a URL change, which is why it is the one that gets
  missed.
- **Aligned `=>` columns and inline comments in PHP samples.** They look tidy in
  the editor and are exactly what Pint rejects; the project's own code never
  has them.
- **A procedure written as prose.** "Go to Configure, open General, enable X
  and save" reads fine to the author and is unusable to someone doing it with
  the admin open beside them.
- **Marketing language on a technical page, and a technical page's caution on
  a marketing one.** The AI overview may say "generative AI"; the page that
  documents `magic_ai()->generateContent()` says what the method returns.
- **A docs skill that describes yesterday's admin.** When a menu path, label or
  group changes in the code, the guide's paths change with it; grep the guide
  for the old label before calling the code change done.

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
