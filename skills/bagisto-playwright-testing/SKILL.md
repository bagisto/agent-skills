---
name: bagisto-playwright-testing
description: Use when writing, changing or debugging a Bagisto end-to-end test — Playwright specs, page objects, ACL role coverage, fixtures, or a failing E2E run in CI. Trigger phrases include "playwright", "e2e", "end to end", "spec.ts", "page object", "browser test", "flaky test", "shard".
---

# Playwright Testing

Bagisto's end-to-end suites live in **two independent Playwright projects**, one
per package, each with its own config, fixtures and page objects:

```
packages/Webkul/{Admin,Shop}/tests/e2e-pw/
├── playwright.config.ts    # testDir ./tests, workers 1, retries 0
├── setup.ts                # adminPage / shopPage fixtures
├── pages/                  # page objects (BasePage subclasses)
├── tests/                  # *.spec.ts, grouped by admin menu section
├── utils/                  # faker.ts, admin.ts (login)
└── data/                   # fixture files for uploads
```

Run from the package directory, never the repo root:

```bash
cd packages/Webkul/Admin
npm install && npx playwright install --with-deps chromium
npx playwright test --config=tests/e2e-pw/playwright.config.ts
npx playwright test --config=tests/e2e-pw/playwright.config.ts -g "create a category"
```

## The base URL comes from `.env`, not `BASE_URL`

`playwright.config.ts` loads the app's `.env` and reads **`APP_URL`**:

```ts
baseURL: `${process.env.APP_URL}/`.replace(/\/+$/, "/")
```

Nothing in either project reads `BASE_URL`. The CI workflows set a `BASE_URL`
env var **and it is ignored** — they work because the same step rewrites
`APP_URL` in `.env` with `sed`. Passing `BASE_URL=…` on the command line does
nothing; to point a run at another host, change `APP_URL`.

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

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
