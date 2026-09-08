# Suite architecture and where code goes

## Contents

- [The layout](#the-layout)
- [Why the shared layer must stay dependency-free](#why-the-shared-layer-must-stay-dependency-free)
- [Where a new piece of code belongs](#where-a-new-piece-of-code-belongs)
- [The wrapper pattern](#the-wrapper-pattern)
- [What the suites still do not share](#what-the-suites-still-do-not-share)
- [Timeouts and configuration](#timeouts-and-configuration)

## The layout

Three independent Playwright projects, one per package, plus a small root-level
layer of dependency-free helpers all three import through `@shared/*`.

```
tests/e2e-pw/helpers/       # shared, dependency-free — imported as @shared/*
├── env.ts                  # readEnv() → baseUrl, adminEmail, adminPassword, timezone, headed
├── faker.ts                # uniqueStamp, generateName, generateEmail, generateSlug, …
├── paths.ts                # createE2ePaths(e2eRootPath)
├── prices.ts               # formatPrice
└── regex.ts                # escapeRegExp

packages/Webkul/{Admin,Shop,Installer}/tests/e2e-pw/
├── playwright.config.ts    # testDir ./tests, workers 1, retries 0, chromium
├── setup.ts                # adminPage / shopPage fixtures (Installer has neither)
├── tsconfig.json           # strict; @pages/* @utils/* @data/* @shared/*
├── pages/                  # BasePage.ts + page objects (admin/ and shop/)
├── tests/                  # *.spec.ts — Admin by menu, Shop by customer journey
├── utils/                  # package-local helpers, and the wrappers over @shared/*
└── data/                   # fixture files for uploads
```

## Why the shared layer must stay dependency-free

CI runs `npm install` inside `packages/Webkul/<project>` only — there is no root
`node_modules`, in CI or locally. Anything under `tests/e2e-pw/helpers/`
therefore has to run with no imports of its own: no `@playwright/test`, no
`dotenv`, no third-party package. Pure TypeScript over `process.env`, strings,
numbers and dates.

Breaking this does not fail locally if you happen to have something installed —
it fails in CI, on every shard at once, at import time.

## Where a new piece of code belongs

That constraint, not taste, decides it:

| Put it in | When |
|---|---|
| `tests/e2e-pw/helpers/` | Genuinely useful to more than one suite **and** dependency-free — value generation, string/price formatting, environment parsing, path arithmetic |
| `<package>/tests/e2e-pw/utils/` | It needs a package dependency, or encodes something only that suite knows |
| `<package>/tests/e2e-pw/pages/` | It drives a screen |

Search before adding anything: reuse → extend → refactor → create new. The
inventory of what already exists is in [investigation.md](investigation.md).

## The wrapper pattern

`utils/env.ts` is the pattern to copy: shared `readEnv()` does the parsing and
validation, and the package's `utils/env.ts` owns the `dotenv` call — the
dependency stays where the dependency is installed.

```ts
import dotenv from "dotenv";
import { readEnv } from "@shared/env";
import { resolveEnvPath } from "./paths";

const envPath = resolveEnvPath();

if (envPath) {
    dotenv.config({ path: envPath });
}

export const env = readEnv();
```

`utils/faker.ts` does the same, re-exporting `@shared/faker` and adding
package-local generators (`generateSKU` in Admin, `generateLocation` in Shop), so
specs import everything from one barrel. A pure helper with no package-local
variant, such as `escapeRegExp`, is imported straight from `@shared/regex` by the
page objects that need it.

## What the suites still do not share

**No page objects, fixtures or specs.** Each suite carries page objects for
whatever screens it must drive, including the other side's — that is what keeps
them independently runnable, and it is why `ProductCreatePage` genuinely exists
twice.

Never import across package boundaries. If both suites need the same
*dependency-free* logic it belongs in `@shared/*`; if it needs Playwright, each
suite keeps its own copy and you make the change twice.

## Timeouts and configuration

Per-test timeouts are 60 s in Admin, 240 s in Shop (plus a 2 h global cap) and
300 s in Installer; `expect` waits 30 s in all three. A single long flow raises
its own with `test.setTimeout(...)`; never raise the config.

`utils/env.ts` is the only place `process.env` is read and `utils/paths.ts` owns
every path — never read either directly. The full environment contract is in
[troubleshooting.md](troubleshooting.md), and the timezone half of it in
[time-and-timezone.md](time-and-timezone.md).
