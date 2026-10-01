# What every site has in common

Every Bagisto documentation site is a VitePress site with the same shape:

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

## Learn the site rather than assuming it

The sites differ in ways that matter and that change over time, so check rather
than recall:

```bash
grep -n "app.component(" .vitepress/theme/index.ts        # custom components, e.g. an image viewer
grep -ohE "'/[0-9][^/]*" .vitepress/_redirects.ts | tr -d "'" | sort -u   # legacy version prefixes
```

The second one matters most: a page that moves needs its redirect repointed
under **every** prefix that site carries, and the count is not the same between
repositories. See [publishing.md](publishing.md).
