# Adding, moving and deleting pages

Four things describe a page's existence, and they are edited in four different
files. Miss one and the site is quietly inconsistent — a page nobody can reach,
a redirect to a 404, an index that disagrees with the sidebar.

| | Lives in |
|---|---|
| The page | `src/<section>/<page>.md` |
| Its place in the navigation | `sidebar` (and sometimes `nav`) in `.vitepress/config.mts` |
| Its old URLs | `.vitepress/_redirects.ts` |
| Its machine-readable entry | `src/public/llms.txt`, `src/public/llms-full.txt` |

Everything here is the same across the documentation repositories. What differs
between them — the legacy version prefixes, the image component — is called out
where it matters, and always with the command to check rather than a value to
remember.

## Adding a page

1. Create `src/<section>/<page>.md`, kebab-case filename.
2. Add a sidebar entry to the matching group in `.vitepress/config.mts`:
   ```ts
   { text: "Themes", link: "/appearance/themes" },
   ```
   The group's `text` is the heading; a new group takes `collapsed: false` like
   its neighbours. A page that also deserves top-bar placement goes in `nav` as
   well; most do not.
3. Add the page to `llms.txt`, and its content to `llms-full.txt`.
4. `npm run docs:build`.

Where a site generates its sitemap in a `buildEnd` hook, it is built from the
files on disk and needs no edit — but a tracked `src/public/sitemap.xml` is a
build artefact of a previous run, not a source file, and hand-editing it
achieves nothing.

## Any change to an existing page's URL

**This is the rule that gets forgotten.** Redirects are easy to remember when
deleting a page and easy to miss everywhere else — but the reader's bookmark
breaks the same way whichever edit caused it.

A page's URL is `/<folder>/<filename-without-.md>`. **Anything that changes
either half changes the URL**, and every one of these needs a redirect:

| The edit | Example |
|---|---|
| Renaming the file | `captcha.md` → `google-captcha.md` |
| Fixing a typo or wording in the filename | `qoute.md` → `quote.md` |
| Moving it to another section folder | `settings/themes.md` → `appearance/themes.md` |
| Renaming a section folder | everything inside it moves |
| Splitting one page into two | the original URL must land on one of them |
| Merging two pages into one | the URL that disappears needs redirecting |
| Deleting it | below |

Renaming a file to fix its spelling feels like tidying rather than a URL change,
which is exactly why it is the one that ships without a redirect.

Whenever the URL changes, do both halves:

1. **Add** `'<old-path>': '<new-path>'` to `.vitepress/_redirects.ts`, so links
   already published to the old URL keep working.
2. **Repoint** every existing redirect that aimed at the old path — under every
   legacy prefix the site carries — or they now point at a page that is gone.

Miss the second half and the build still succeeds: it cheerfully writes a
redirect to a 404. Nothing warns you. The checks at the end of this file are
what catch it.

### Changing a heading

Headings are anchors, and a link to `#nothing-goes-live-until-you-publish` lands
at the top of the page once that heading is reworded. `_redirects.ts` cannot fix
a fragment, since the browser never sends it to the server.

So rename headings deliberately, not in passing. When a heading that is widely
linked has to change — or a page is split — redirect the page URL to the new
anchor, which is a pattern the sites already use:

```ts
'/2.3/introduction/requirements.html': '/getting-started/before-you-start.html#system-requirements',
```

## Moving a page

A move is a delete and an add that must not lose the old URL.

1. `git mv` the page to its new folder.
2. Move its images to `src/public/images/<new-section>/` and update every image
   reference on the page.
3. Move the sidebar entry to the new group and update its `link`.
4. Repoint every redirect that aimed at the old path.
5. Add a redirect from the old path to the new one.
6. Update `llms.txt` and `llms-full.txt`.

## Deleting a page

Do not delete first and look afterwards. Find out what points at it:

```bash
grep -n "': '/settings/themes'," .vitepress/_redirects.ts   # redirects aimed at it
grep -rn "(/settings/themes)" src --include=*.md            # inbound links
grep -n "settings/themes" .vitepress/config.mts             # sidebar entry
```

Then, in one change:

1. Repoint every redirect found above at the page that now holds the content —
   not at the parent section, and not at the home page. A redirect landing
   somewhere vague is only marginally better than the 404 it replaced.
2. Repoint or remove any inbound links from other pages.
3. Remove the sidebar entry.
4. Delete the file, and delete images used only by it.
5. Remove it from `llms.txt` and `llms-full.txt`.
6. `npm run docs:build` and confirm the page is gone from `.vitepress/dist/`
   while every old URL still resolves.

### Never delete a page that is holding a URL open

Some pages exist only to keep a legacy path resolving — including, on the
developer side, a tree of **zero-byte markdown files** left behind when URLs
were flattened. They look like clutter and they are load-bearing: deleting one
takes its URL down, and every external link to it breaks.

Do not remove them, and do not remove them as tidying while editing the page
they shadow. A redirect is the better mechanism for anything new — it sends the
reader onward instead of merely avoiding a 404 — but replacing an existing
URL-holder is a deliberate change of its own, never a side effect.

### Replace a stub with a redirect — in that order

The tempting shortcut when a page moves is to leave a one-line stub saying "this
has moved". It is worse than a redirect: it stays in the sidebar, it ranks in
search, and it costs the reader a click to learn they are in the wrong place.

So a stub should become a redirect — but **the redirect goes in first**. The
stub is holding its URL open, and deleting it before `_redirects.ts` covers that
URL turns a working page into a 404 in the window between the two edits, and
permanently if the second edit is forgotten.

## How redirects work

`.vitepress/_redirects.ts` exports a flat map of old path to new path. A
`buildEnd` hook in `.vitepress/config.mts` writes one HTML redirect file per
entry into `.vitepress/dist` and logs each:

```
✅ Redirect created: /2.3.0/settings/themes.html -> /appearance/themes
```

Two forms of key, and they build to different places:

| Key | Builds to |
|---|---|
| `'/2.3.0/settings/themes.html'` | that exact file |
| `'/2.3.0/introduction/'` | `…/index.html` under that directory |

A target may carry a fragment, which is how a page that was split gets its
readers to the right heading. Wildcards are skipped with a warning, so a `*` key
does nothing.

**Each site carries its own set of legacy version prefixes, and the sets are not
the same.** Discover them rather than assuming:

```bash
grep -ohE "'/[0-9][^/]*" .vitepress/_redirects.ts | tr -d "'" | sort -u
```

A page that moves needs its redirect repointed under **every** prefix that
returns. Repointing all but one is the usual mistake, and nothing catches it.

## Verifying

`npm run docs:build` catches a broken VitePress link. It does **not** catch a
URL your change removed, a redirect aimed at a deleted page, or a page missing
from the sidebar. Check all three.

**Every URL your change removed is covered by a redirect.** This is the one that
catches a rename shipped without one — it compares the working tree against
`HEAD`, so run it before committing:

```bash
git diff --name-status -M HEAD -- src | grep -E '^(D|R)' | grep -v '/public/' |
while read -r status old new; do
    url="/${old#src/}"; url="${url%.md}"
    grep -q "'$url'" .vitepress/_redirects.ts \
        && echo "ok           $url" \
        || echo "NO REDIRECT  $url"
done
```

Every line must read `ok`. A `NO REDIRECT` means that URL is live today and will
404 the moment this ships.

Note what it compares: the **current** URL, not the versioned legacy ones.
Repointing `/2.3.0/settings/themes.html` does nothing for `/settings/themes`,
which was equally live and equally bookmarked. Both need covering, and adding
the versioned entries while forgetting the current one is the easy mistake —
this check exists because it was made.

Add the key in both forms, since either can appear in a link:

```ts
'/settings/themes': '/appearance/themes',
'/settings/themes.html': '/appearance/themes',
```

**Every redirect target resolves to a built page.** Mind that some targets
already end in `.html`, and some carry a fragment:

```bash
python3 - <<'PY'
import re, io, os
s = io.open('.vitepress/_redirects.ts', encoding='utf-8').read()
bad = []
for t in sorted(set(re.findall(r"':\s*'(/[^']+)'", s))):
    if '*' in t:
        continue
    base = t.split('#')[0]
    base = base[:-5] if base.endswith('.html') else base
    if not any(os.path.exists(p) for p in (
        f".vitepress/dist{base}.html", f".vitepress/dist{base}/index.html")):
        bad.append(t)
print('broken redirect targets:', bad or 'none')
PY
```

**No page is missing from the sidebar.** A page absent from it is unreachable.
Exclude any directory of zero-byte URL-holders, which are expected to be absent:

```bash
python3 - <<'PY'
import re, io, os
cfg = io.open('.vitepress/config.mts', encoding='utf-8').read()
links = set(re.findall(r"link:\s*['\"](/[^'\"]+)['\"]", cfg))
pages = {
    '/' + os.path.relpath(os.path.join(r, f), 'src')[:-3]
    for r, _, fs in os.walk('src') if 'public' not in r
    for f in fs
    if f.endswith('.md') and os.path.getsize(os.path.join(r, f)) > 0
}
print('orphans:', sorted(p for p in pages - links if not p.endswith('index')) or 'none')
PY
```

All three should come back clean before the change is done.

## Deployment

A `deploy.sh` at the repository root builds and force-pushes `.vitepress/dist`
to the `gh-pages` branch. It is a publish, not a commit — run it only when the
change is meant to go live, and never as a way of checking your work.
`npm run docs:build` is how you check your work.
