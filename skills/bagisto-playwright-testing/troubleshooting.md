# Troubleshooting a Playwright failure

## Contents

- [Read the failure before changing anything](#read-the-failure-before-changing-anything)
- [Strict mode violations](#strict-mode-violations)
- [Clicks that never land](#clicks-that-never-land)
- [Locators that match nothing](#locators-that-match-nothing)
- [Failures caused by leftover data](#failures-caused-by-leftover-data)
- [Environment faults mistaken for bugs](#environment-faults-mistaken-for-bugs)
- [A test that passes when it should not](#a-test-that-passes-when-it-should-not)

## Read the failure before changing anything

Every failure writes a directory under `tests/e2e-pw/test-results/<test-name>/`
containing `error-context.md` (the error plus a page snapshot), a full-page
screenshot, and `trace.zip`.

```bash
awk '/# Error details/,/# Page snapshot/' test-results/<dir>/error-context.md
npx playwright show-trace test-results/<dir>/trace.zip
```

The error text names the cause far more often than the stack does. Read it
before touching the test.

## Strict mode violations

`resolved to N elements` means the locator is not scoped, not that Playwright is
being strict for no reason. In an admin list every row carries the same markup,
so a page-level locator matches every row.

```ts
// Wrong — every row has a Delete item in its dropdown
await page.getByText("Delete", { exact: true }).click();

// Right — scope to the row first
const row = this.sectionRow(name);
await row.locator("button.icon-dots").click();
await row.getByText("Delete", { exact: true }).click();
```

Two other sources of the same error:

- **A container that also matches.** A row selector like `div.border-b` also
  matches the drawer header showing the same record's name. Prefer a selector
  unique to the list (`div[data-draggable]`).
- **The debug bar.** With `APP_DEBUG=true` and Laravel Debugbar enabled, the
  flash message is rendered a second time inside a `sf-dump` panel, so
  `getByText("… successfully")` resolves to two elements locally and one in CI.
  Set `DEBUGBAR_ENABLED=false` while running E2E locally.

## Clicks that never land

`element intercepts pointer events` names the element on top. In Bagisto that is
almost always an open drawer, modal or overlay.

Creating a record often opens its edit drawer immediately, which then covers the
list. Close it before acting on the list behind it:

```ts
await this.closeDrawerButton.click();          // span.icon-cross
await expect(this.publishActiveButton).toBeHidden();
```

Sortable lists are driven by pointer events, so `dragTo` is unreliable. Take the
handle and move it:

```ts
const handle = this.sectionRows.nth(from).locator("span.section-handle");
const target = await this.sectionRows.nth(to).boundingBox();

await handle.hover();
await this.page.mouse.down();
await this.page.mouse.move(target.x + target.width / 2, target.y + target.height / 2, { steps: 12 });
await this.page.mouse.up();
```

Note that a stray click near a drag handle can start a real drag and reorder the
list. If a spec's later assertions drift for no visible reason, suspect this.

## Locators that match nothing

- **Icon-font glyphs pollute the accessible name.** A tile rendered as an icon
  span plus a label span does not answer to
  `getByRole("button", { name: "Static Content" })`. Target the label:
  `locator("span").filter({ hasText: /^Static Content$/ })`.
- **Schema-driven fields have no `name` attribute.** Vue components that render
  from a schema bind with `v-model`, so there is nothing to select by name.
  Address them through the label above the control:
  ```ts
  this.page.locator("p").filter({ hasText: /^Title$/ })
      .locator("xpath=following-sibling::*[self::input or self::textarea][1]")
  ```
- **The element is behind a `v-if` that has not resolved.** Wait for a stable
  anchor (`await this.createForm.waitFor()`), not a fixed timeout.
- **The bundle is stale.** After any frontend change run
  `npm run build` in the package, or the browser loads the previous JS and the
  component you are targeting does not exist yet.

## Failures caused by leftover data

The E2E suites share one database and **do not roll back**. Every record a run
creates is still there for the next run.

Symptoms: an assertion on a count (`Failed asserting that 42 is identical to 2`),
on "the first row", or on a total that grew between two runs of the same command.

Fixes, in order of preference:

1. Assert on the uniquely-named record you created, never on a count or an index.
2. If a spec must leave the app in a particular state, put the state back.
3. When cleaning dev data by hand, **delete by explicit id only.** A predicate
   like `name LIKE '% Copy'` will eventually match something a person created.

## Environment faults mistaken for bugs

- **`APP_URL` is the base URL.** Neither project reads `BASE_URL`, despite CI
  setting it. If every test 404s or hits the wrong host, check `.env`.
- **The app must be running and seeded.** CI runs `bagisto:install`, seeds the
  product table and runs `indexer:index --mode=full` before the first spec.
- **Browsers must be installed where the tests run** —
  `npx playwright install --with-deps chromium`. In a containerised workspace,
  decide deliberately whether the run happens on the host or in the container,
  and install the browsers there.

## A test that passes when it should not

The most expensive failure mode is a regression test that never guarded
anything. After writing one, **revert the fix and confirm the test fails.**

Two ways a test is born dead in this codebase:

- **The seeded data does not reproduce the bug.** A reorder test cannot detect a
  gapped-`sort_order` bug when the seeder writes a contiguous `1..N`, so it
  passes with and without the fix. If the condition cannot be created through
  the UI, cover it in Pest, where the fixture can be set up directly — and say
  so in the test name rather than implying a guarantee the test does not give.
- **The assertion is weaker than the claim.** Asserting that a badge cleared does
  not prove the value reverted. Assert the observable state itself.
