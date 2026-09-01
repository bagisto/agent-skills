---
name: bagisto-playwright-testing
description: Use when writing, changing or debugging a Bagisto end-to-end test — Playwright specs, page objects, ACL role coverage, fixtures, or a failing E2E run in CI. Trigger phrases include "playwright", "e2e", "end to end", "spec.ts", "page object", "browser test", "flaky test", "shard".
---

# Playwright Testing

Bagisto's end-to-end suites live in **three independent Playwright projects**,
one per package, each with its own config, fixtures and page objects:

```
packages/Webkul/{Admin,Shop,Installer}/tests/e2e-pw/
├── playwright.config.ts    # testDir ./tests, workers 1, retries 0
├── setup.ts                # adminPage / shopPage fixtures
├── tsconfig.json           # 2.5 only — strict; `npm run typecheck`
├── pages/                  # page objects (BasePage subclasses)
├── tests/                  # *.spec.ts, grouped by admin menu section
├── utils/
│   ├── env.ts              # 2.5 only — the only place process.env is read
│   ├── paths.ts            # 2.5 only — every path the suite knows
│   └── faker.ts, admin.ts  # data helpers, login
└── data/                   # fixture files for uploads
```

On 2.4 the same three suites exist without `tsconfig.json`, `utils/env.ts` or
`utils/paths.ts` — `playwright.config.ts` carries that work itself.

Run from the package directory, never the repo root. **The two Bagisto lines are
invoked differently — check `package.json` before choosing a form.**

**2.5** exposes package scripts:

```bash
cd packages/Webkul/Admin
npm install && npm run install:browsers
npm run test:e2e
npm run test:e2e -- -g "create a category"
npm run test:e2e -- --shard=1/10
```

`test:e2e:headed`, `:ui`, `:debug` and `:report` mirror the Playwright flags;
`typecheck` and `format` are local tools, not CI gates, because neither is yet
clean on the existing specs.

**2.4** has no such scripts — invoke Playwright directly:

```bash
npx playwright install --with-deps chromium
npx playwright test --config=tests/e2e-pw/playwright.config.ts
```

## Where configuration comes from

**2.5** reads and validates every value once in `utils/env.ts` — base URL from
`APP_URL` falling back to `BASE_URL`, plus `BAGISTO_ADMIN_EMAIL`,
`BAGISTO_ADMIN_PASSWORD` and `HEADED`. Set no URL and it fails immediately with
a directed message rather than navigating to the string `"undefined/"`. Never
read `process.env` from a config, spec, page object or fixture.

`utils/paths.ts` owns every path, including `ADMIN_AUTH_STATE_PATH` and
`ensureStateDir()`. It finds the application by searching upward for `artisan`
rather than counting `../`, and prefers a suite-local `tests/e2e-pw/.env` when
one exists — so the folder keeps working if it moves. Never hardcode a
parent-walk, and never import a path from `playwright.config.ts`.

**2.4** has neither file: `playwright.config.ts` loads the app `.env` itself and
reads `APP_URL` only. `BASE_URL` is set by CI and ignored — to retarget a run,
change `APP_URL`.

## Reference files

| File | Load when |
|---|---|
| [authoring.md](authoring.md) | Writing a new spec or page object — structure, fixtures, ACL tests, naming |
| [troubleshooting.md](troubleshooting.md) | A test fails, hangs, or passes when it should not |

## Non-negotiables

- **The suite shares one database and does not roll back.** Unlike Pest, an E2E
  run leaves every record it creates. Write assertions that survive that:
  scope to the row you created, never to a global count or a list position.
- **`workers: 1`, `retries: 0`, `fullyParallel: false`.** Specs run in file
  order within a shard, so a spec that leaves the app in a changed state
  (a reordered list, a disabled record) affects the next one. Put the state back
  or assert only on what you made.
- **CI shards each project 10 ways** (`--shard=i/10`). A spec may not depend on
  another spec having run — shards split by file.
- **Admin auth is cached** to `.state/admin-auth.json` by the `adminPage`
  fixture and reused across specs. Do not log in by hand in a spec.
- **Rebuild assets before running** after any frontend change, or the browser
  loads the previous bundle and the failure will look like a test bug.
- **No comments anywhere under `tests/e2e-pw/`** — no `//`, no `/* */`, no
  docblock, in specs or page objects. Put the reason in a method name instead.
- **Generate test data inside `beforeEach`, never at module scope.** One
  module-scope `Date.now()` gives every test in the file the same SKU, and the
  file only passes while cleanup never misses.
- **Cleanup deletes what it made, and a failed step never skips the next one** —
  wrap the teardown so the product is removed even when the rule delete fails.
- **Filenames are lower-kebab** (`buy-x-get-y-free.spec.ts`), and **a file that
  declares a class is named exactly for it** — `CatalogAclPage.ts`, not
  `catalog.ts`. Describe and test titles are lower case with single spaces.

## Writing a test — the shape

```ts
import { test } from "../../setup";
import { CategoryPage } from "../../pages/admin/catalog/CategoryPage";

test.describe("category management", () => {
    test("should create a category", async ({ adminPage }) => {
        const categoryPage = new CategoryPage(adminPage);

        await categoryPage.createCategory();
    });
});
```

The spec names the intent; the page object owns every locator. A spec that
contains a CSS selector belongs in a page object instead — see
[authoring.md](authoring.md).

## Common mistakes

- **Asserting a global count.** `meta.total`, "the first row", "3 sections" —
  all break as soon as another spec adds a record. Assert on the named thing you
  created.
- **A hardcoded fixture value that the run consumes.** A spec that subscribes
  `guest@example.com` and asserts "successfully subscribed" passes once and
  fails on every later run against the same database, because the record it
  needs absent is the one it just created. Generate the value, or delete it
  again. The symptom looks like a broken feature, not a broken test.
- **An unscoped locator that matches many rows.** Every row of a list carries the
  same action markup, so `getByText("Delete")` resolves to N elements and fails
  strict mode. Scope to the row first.
- **Trusting a green new test.** After writing a regression test, revert the fix
  and confirm it fails. On seeded data many assertions hold either way.
- **Assuming a Vue tile's accessible name is its label.** Icon-font glyphs land
  in the accessible name, so `getByRole("button", { name: "Static Content" })`
  can match nothing. Target the label element.
- **Forgetting an open drawer or modal covers the page.** Clicks on the list
  behind it are intercepted; close it first.
- **Treating a server-rendered element as "form ready".** Blade paints the input
  before Vue mounts and initialises the model, so a value typed in between is
  discarded and the save fails validation with that field "required" while the
  text is still on screen. A fixed `waitForTimeout` only moves the race.

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
