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
| [site-structure.md](site-structure.md) | Finding your way round a docs repository — layout, commands, per-site differences |
| [common-mistakes.md](common-mistakes.md) | Auditing a finished change |

Every site is a VitePress site: pages under `src/`, the sidebar in
`.vitepress/config.mts`, legacy URLs in `.vitepress/_redirects.ts`. Preview with
`npm run docs:dev`; `npm run docs:build` is the gate. The sites differ in their
components and redirect prefixes, so learn the one you are in —
[site-structure.md](site-structure.md).

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
- **AI terminology is earned by the implementation.** "Generative AI" is for
  features that produce content — pages and headings say "Generative AI (Magic
  AI)", and "Magic AI" alone is kept for the admin's own labels and the package.
  "Agentic AI" is for features where an agent acts through tools (WebMCP,
  coding agents using the skills). Never claim autonomy the code does not have:
  Magic AI applies nothing without an admin. See the AI sections of both
  reference files.
- **The user guide follows the merchant's journey**, and Configure follows the
  admin's own Configuration screen; the marketplace guide has three readers;
  configuration pages start from the `config('core')` tree, not the old pages.
  Each has its section in [user-guide.md](user-guide.md). The developer
  documentation's navigation is **not** reorganised unless the user asks.
- **Finish with an independent audit.** After editing, verify the result as a
  reviewer who did not write it: every claim against the code, every sample
  through Pint, every link and image resolved, the sidebar and `llms.txt`
  consistent, then the build, then [common-mistakes.md](common-mistakes.md). A
  change that has only been written has not been checked.
- **`llms.txt` and `llms-full.txt` are written by hand.** Nothing generates
  them. Adding, moving or deleting a page means editing them too.
- **The build is the gate.** `npm run docs:build` reports each redirect it
  writes. A change that has not been built has not been checked.

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
