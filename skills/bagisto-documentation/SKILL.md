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
- **Verify claims against the codebase, not memory.** A confidently wrong
  sentence is worse than no page, because it is believed. Open the file, run the
  command, check the string.
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

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
