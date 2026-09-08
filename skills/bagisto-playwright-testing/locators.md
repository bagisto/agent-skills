# Locators and synchronisation

## Contents

- [Choosing a locator](#choosing-a-locator)
- [What is stable in Bagisto](#what-is-stable-in-bagisto)
- [Scope before you select](#scope-before-you-select)
- [Positional locators](#positional-locators)
- [Verify the library before you change a selector](#verify-the-library-before-you-change-a-selector)
- [Bagisto markup that defeats the obvious locator](#bagisto-markup-that-defeats-the-obvious-locator)
- [Synchronisation](#synchronisation)
- [Diagnosing "not ready yet"](#diagnosing-not-ready-yet)

## Choosing a locator

Prefer locators that describe the element the way a user perceives it:

```
getByRole()  getByLabel()  getByPlaceholder()  getByText()  getByTestId()
```

then stable semantic attributes, then structural CSS, then XPath.

This is a preference, not a ranking to apply mechanically. Choose on four
properties, in this order:

1. **Uniqueness** — does it resolve to exactly the intended element?
2. **Stability** — does it survive a plausible redesign of this screen?
3. **Meaning** — does it say *what* the element is, so a reader understands the
   test?
4. **Scope** — is it anchored to the container the behaviour lives in?

A `getByText` that matches nine rows is worse than an `input[name="sku"]` that
matches one. Never pick a locator because it is short, and never pick one
because it made a strict-mode error go away.

## What is stable in Bagisto

**There are no test ids.** `data-testid` appears zero times in the Admin and
Shop Blade views. `getByTestId()` is therefore not available to you unless you
add the attribute to core markup — which is a real change to the application,
worth doing only when no stable locator exists, and worth saying so in your
summary when you do.

What *is* stable, in practice:

| Locator | Why it holds | Example |
|---|---|---|
| `getByRole` with a name | Accessible names come from user-facing labels | `getByRole("button", { name: "Save Section" })` |
| `getByPlaceholder` | Placeholders come from lang files; the storefront uses them heavily | `getByPlaceholder("Search products here")` |
| `input[name="…"]` | The `name` is the request payload key — the server contract, not styling | `input[name="sku"]`, `input[name="catalog[products][storefront][products_per_page]"]` |
| `label[for="…"]` | Config toggles have no clickable input; the `for` is the same contract | `label[for="catalog[products][settings][compare_option]"]` |
| A row filtered by a unique generated name | The name is data the test owns | `.filter({ hasText: name })` |
| A semantic container id | Set deliberately in the Blade | `#section-create-form`, `#review-tab` |

What is not stable, and shows up in the suite today: Tailwind utility chains
(`div.border-b`), icon-font classes used as identity (`.icon-uncheckbox`,
`.icon-bin`), and anything positional.

Icon classes are a grey area. `span.icon-cross` is how a close control is
identified across this codebase and there is no better handle; that is
acceptable *inside a scoped container*. `.icon-delete` at page level, matching
every row's delete control, is not.

### The admin DataGrid has no table semantics

`components/datagrid/table.blade.php` renders a CSS grid of `div`s, not a
`<table>`. There is no `role="row"`, no `<tr>`, no `<td>` — so
`getByRole("row", …)`, `getByRole("cell", …)` and `getByRole("table")` match
nothing on any admin listing, and the suite uses none of them.

The row hooks that do exist:

| Hook | Markup |
|---|---|
| A body row | `div.row` carrying `.border-b`; the header row is `div.row.datagrid-head` |
| The empty state | a `div.row` containing the "No Records Available." text |
| A record's mass-action checkbox | `input[name="mass_action_select_record_<id>"]` — stable and record-scoped, when you know the id |

So a row locator is a filtered container, and it must exclude the head:

```ts
private row(text: string) {
    return this.page
        .locator("div.row:not(.datagrid-head)")
        .filter({ hasText: text });
}
```

Filter on a value the test owns — a generated SKU, name or email — and search
the grid for it first, so the filter has exactly one candidate to match.

## Scope before you select

Every row of an admin grid carries identical markup, and Bagisto often renders
the same record twice — once in the list and again in the drawer that just
opened over it. A page-level locator therefore matches N elements and fails
strict mode.

This resolves to every row's delete item and fails strict mode:

```ts
await page.getByText("Delete", { exact: true }).click();
```

Scope to the row that carries the name your test owns, then act inside it:

```ts
const row = this.sectionRow(name);

await row.locator("button.icon-dots").click();
await row.getByText("Delete", { exact: true }).click();
```

**`.first()` is not a fix for a strict-mode violation.** It converts "this
locator is ambiguous" into "this test asserts about an element chosen by
accident". When strict mode complains, the locator is under-scoped; scope it.

The `:visible` pseudo-class (`button.primary-button:visible`) is the suite's
usual workaround for duplicate markup. It works, but it says "whichever one is
on screen" rather than "the save button of this form". Prefer scoping to the
form, drawer or row; reach for `:visible` only when the duplicate is genuinely
outside any container you can name.

## Positional locators

`.nth()`, `.first()` and `.last()` may identify a business entity **only when
position is the behaviour under test**:

- a drag-and-drop reorder, where the assertion is *which row is now first*;
- a "most recent order appears at the top" guarantee;
- a carousel's first slide.

In every other case a position is a guess about what other tests and other
people left in the database. Find the record by the name the test gave it. See
[test-data.md](test-data.md).

## Verify the library before you change a selector

A locator that looks wrong may be right for *that* package. Never change one by
reasoning from a sibling suite, from a library's current documentation, or from
what the class name "should" be. Check what the package actually resolves and,
where you can, what the DOM actually contains.

The case that proves it: Flatpickr is on two different major versions in one
repository.

| Package | Declares | Resolves to | Disabled-day class |
|---|---|---|---|
| Admin | `flatpickr: ^4.6.13` directly | **4.6.13** | `.flatpickr-disabled` |
| Shop, Installer | no direct dependency; `vue-flatpickr: ^2.3.0` | **2.6.3** | `.disabled` |

So `.flatpickr-day:not(.disabled)` is correct on the storefront and wrong in
admin, and the modern-looking `.flatpickr-disabled` matches nothing in Shop. A
"fix" applied across both on the strength of Admin's version silently widened a
Shop locator from 23 matching days to all 36 — it did not fail, it just stopped
discriminating.

Before editing a locator that depends on a third-party widget:

```bash
node -e "console.log(require('./packages/Webkul/<Pkg>/node_modules/<lib>/package.json').version)"
```

and confirm the class or structure in the rendered DOM rather than assuming. A
transitive dependency has no entry in `package.json` at all, so reading the
manifest alone is not enough.

## Bagisto markup that defeats the obvious locator

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

  This is one of the few places XPath earns its keep. Keep it in a private
  locator method so exactly one place needs updating.
- **TinyMCE lives in an iframe.** Use the `fillInTinymce` fixture helper rather
  than reaching into the frame yourself.
- **Flash messages render twice with Laravel Debugbar on**, so
  `getByText("… successfully")` resolves to two elements locally and one in CI.
  Set `DEBUGBAR_ENABLED=false` for local E2E runs rather than adding `.first()`.

## Synchronisation

Wait for the state transition the application actually makes. Never for a
duration.

**Prefer, in this order:**

1. **A web-first assertion on the outcome.** `expect(locator).toBeVisible()`,
   `toHaveText`, `toHaveValue`, `toHaveCount(0)`, `expect(page).toHaveURL(…)`.
   These retry until the expect timeout — 30 s in all three suites — and they
   double as the assertion, so they cost nothing extra.
2. **A wait on a stable anchor** before interacting — `await
   this.createForm.waitFor()` — when the thing you need is not the thing you are
   asserting.
3. **`expect.poll`** for a state that has more than two outcomes — "rows
   rendered / empty state / still loading", as `DatagridPage.waitForGrid()` does.
4. **`waitForResponse`**, only when the UI gives no observable signal. The suite
   uses it for the datagrid filter request and for section publishing:

   ```ts
   await Promise.all([
       this.page.waitForResponse((response) =>
           response.url().includes("/sections/publish"),
       ),
       this.publishAllButton.click(),
   ]);
   ```

   Pair it with an assertion on what the response changed. A request completing
   is not the same as the UI having updated.

**Avoid:**

- **`waitForTimeout`, `sleep`, and named delay constants.** There are none left
  in the suites and none should return — every one is either unnecessary or
  hiding a race that will resurface on a slower machine. `const
  CART_WAITING_TIME = 2000` is a fixed delay with a nicer name.
- **`waitForLoadState("networkidle")` as a general-purpose wait.** Playwright
  discourages it, and on Bagisto screens with polling or lazy-loaded widgets it
  either returns too early or costs seconds of dead time. Wait for the element
  that proves the page is ready instead.
- **Adding a wait to fix a flake.** A flake means the test does not know what it
  is waiting for. Find that first.

**The one sanctioned use of `networkidle`** is
`BasePage.waitForBackgroundRequestsToSettle()`, and it exists for a specific
application behaviour rather than for convenience: Bagisto's shop API routes run
in the `web` middleware group, so in-flight `/api/*` requests save the session and
can consume a Laravel flash message before the page that should display it
renders. Settling those requests before a state-changing submit is waiting for a
real application condition. Call the helper; do not open-code `networkidle`, and
do not reach for it when a locator assertion would do. The mechanism is in
[troubleshooting.md](troubleshooting.md).

## Diagnosing "not ready yet"

When an interaction lands too early, work out which of these it is before
changing anything:

| Cause | Signal | Fix |
|---|---|---|
| Blade painted the input before Vue mounted | The typed value is on screen but the save 422s with that field "required" | Wait for something only the mounted component renders, then fill |
| A `v-if` has not resolved | Locator matches nothing, page looks right in the screenshot | `await anchor.waitFor()` on the container |
| A drawer or modal is still animating | `element intercepts pointer events` | Assert the overlay is hidden before acting behind it |
| A datagrid request is in flight | Row count is stale, or the empty state is showing | `expect.poll` over rows-vs-empty, or `waitForResponse` on the filter request |
| A dropdown populates asynchronously | `selectOption` throws on a missing value | Assert the option exists, then select |
| A save is async | The next step acts on the old value | Assert the success message *and* the changed value |
| The JS bundle is stale | The component you target does not exist at all | `npm run build` in the package |

The last one is not a synchronisation problem, and no amount of waiting fixes
it. See [troubleshooting.md](troubleshooting.md).
