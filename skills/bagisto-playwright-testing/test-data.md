# Test data, state ownership and cleanup

## Contents

- [The database does not roll back](#the-database-does-not-roll-back)
- [Declare what the test owns](#declare-what-the-test-owns)
- [Generating values](#generating-values)
- [Where values are generated](#where-values-are-generated)
- [Never operate on an arbitrary record](#never-operate-on-an-arbitrary-record)
- [Global settings must be restored](#global-settings-must-be-restored)
- [Cleanup](#cleanup)
- [Test independence](#test-independence)
- [When may a test go around the UI](#when-may-a-test-go-around-the-ui)

## The database does not roll back

Unlike Pest, an E2E run leaves every record it creates, for the next spec and
for the next run of the same spec on the same machine. Every rule below follows
from that one fact.

The two failure shapes it produces:

- **A test that passes once.** It asserts on a condition its own first run
  destroyed — subscribing a hardcoded address and asserting "successfully
  subscribed" works until that address is subscribed, which is now. The symptom
  looks like a broken feature.
- **A test that poisons its neighbours.** It leaves a record, a changed setting
  or a reordered list that the next spec runs against.

## Declare what the test owns

Before writing the body, answer these five in your head — and if any answer is
"something that was already there", fix the design:

| Question | Acceptable answer |
|---|---|
| What does it **create**? | Records it names uniquely and can find again |
| What does it **modify**? | Only records it created |
| What does it **consume**? | Records it created, or genuinely immutable seed data (a country list, a currency) |
| What **global state** does it change? | Ideally none; if any, it restores it |
| What must be **cleaned up**? | Exactly what it created, and nothing else |

"Consume" deserves the most care, and it is the rule most easily broken by
accident: a spec creates a product in a hook, then searches the storefront for a
generic term such as `"simple"` and adds the *first result* — so it does not
exercise the product it made, it exercises whichever seeded product sorts first.
The suites were cleaned of this shape; do not reintroduce it. **If the test
creates data, the test must then use that data by name.**

## Generating values

Generators live in two places, and the split follows the dependency rule in
[SKILL.md](SKILL.md):

- **`tests/e2e-pw/helpers/faker.ts`** (`@shared/faker`) — dependency-free and
  shared by all three suites: `uniqueStamp`, `generateName`, `generateFirstName`,
  `generateLastName`, `generateEmail`, `generatePhoneNumber`, `generateSlug`,
  `generateDescription`, `generateHostname`.
- **`<package>/tests/e2e-pw/utils/faker.ts`** — re-exports `@shared/faker` and
  adds what only that suite needs: `generateSKU`, `generateFullName`,
  `generateCurrencyCode` and `getImageFile` in Admin, `generateLocation` in Shop.

Import from the package barrel (`../utils/faker`), not from `@shared/faker`
directly, so a suite-local generator stays available alongside the shared ones.

Know their limits before trusting them for uniqueness:

| Helper | Pool | Dedupes |
|---|---|---|
| `uniqueStamp()` | `Date.now()` plus a per-process counter | Yes — distinct within and across a run |
| `generateName()` | 144 adjective-noun pairs | Within one process, via a `usedNames` set that appends a discriminator on collision |
| `generateEmail()` | 12 names × 6 domains × a random number | Within one process, via `usedEmails` |
| `generateSlug()` | adjective-noun, delimiter configurable | Within one process, via `usedSlugs` |
| `generateSKU()` (Admin) | `AAA1234` | Not at all |
| `getImageFile()` (Admin) | a random file from `data/images/` | n/a |

The in-process sets make a value unique **within one run**. None of them knows
what is already in the database. So:

- **Where a value must be unique in the database, build it from
  `uniqueStamp()`** — `` `SKU-${uniqueStamp()}` ``, `` `Simple-${uniqueStamp()}` ``.
  `sku` is `Rule::unique` and `url_key` is validated by
  `ProductCategoryUniqueSlug`; a collision with an earlier run's leftover row
  422s with "The sku has already been taken". Prefer it over a bare `Date.now()`,
  which repeats when two values are generated in the same millisecond.
- **Where a value only needs to be distinctive within the page**, a faker name
  is better: it is readable in a failure screenshot, and it is what makes
  `filter({ hasText: name })` resolve to exactly one row.
- **Where the value is the thing under test, make it deterministic.** A boundary
  test asserts on `"999999.99"`, not on a random number — a random value that
  happens to pass says nothing about the boundary.
- **Never generate a value you then assert loosely.** If the test cannot state
  the expected result from the input, the input should not have been random.

## Where values are generated

**Inside `beforeEach`, never at module scope.** A module-scope initialiser runs
once per file, so every test in that file reuses one SKU or name. The second
test then fails on uniqueness the moment cleanup misses once — and since its own
cleanup then fails too, every remaining test in the file fails with it. This is
the single most common cause of a spec file that passes alone and fails in a
suite.

```ts
let generatedSku: string;

test.beforeEach(async ({ adminPage }) => {
    generatedSku = `SKU-${uniqueStamp()}`;
});
```

If a module-scope table needs the value, hold it as a thunk — the table is built
at import time, when the variable is still `undefined`:

```ts
const cases = [{ operator: "==", value: () => generatedSku }];
```

and call the thunk inside the test body, where `beforeEach` has already run —
`value: value()`. Passing `generatedSku` directly into the table gives every
case `undefined`.

**`beforeAll` is not a substitute.** Data created in `beforeAll` is shared by
every test in the file, so the tests are no longer independent and the first one
to modify it breaks the rest. Use it only for state that is genuinely read-only
for all of them, and prefer `beforeEach` when in doubt.

Binary fixtures live in `tests/e2e-pw/data/`, reached through `DATA_PATH` from
`utils/paths.ts`.

## Never operate on an arbitrary record

This is the most common design fault in the existing suites, and it produces
tests that are simultaneously fragile and meaningless.

```ts
await this.customerDetailIcons.first().click();

await this.selectRowBtn.nth(2).click();
await this.selectDelete.click();
```

Both act on whatever currently occupies that position — data another spec
created, or a record a person is using on a shared dev database. The test proves
nothing about the record it cares about, and the cleanup deletes someone else's
row.

The recipe instead: **create it, name it, search for it, act on that row.**

```ts
private row(text: string) {
    return this.page
        .locator("div.row:not(.datagrid-head)")
        .filter({ hasText: text });
}

async deleteCustomer(email: string): Promise<void> {
    await this.open();
    await this.searchFor(email);

    const row = this.row(email);

    await row.locator("span.icon-delete").click();
    await this.agreeButton.click();

    await expect(this.page.getByText("Customer deleted successfully")).toBeVisible();
    await expect(row).toHaveCount(0);
}
```

The admin DataGrid renders rows as `div.row`, not table markup — see
[locators.md](locators.md) before writing a row locator.

The Admin suite's `DatagridPage` base class already does the readiness half
correctly: `openGrid()` waits for Vue to mount and polls until rows render, and
`searchFor()` waits on the filter response. Extend it for a new admin listing
rather than re-deriving those waits, and use `rowWithCell(...)` to address the
row your test owns.

A position is a legitimate target only when position itself is the behaviour
under test — a drag-and-drop reorder, a "first item is featured" rule. Then the
index is the assertion, not a way of finding a record.

## Global settings must be restored

`tests/configuration/**` changes settings that every later spec runs against —
`catalog.products.settings.compare_option`, storefront list mode, review
moderation, guest checkout.

The read-and-restore pattern is now implemented and is the one to copy.
`CheckoutConfigurationPage` exposes `readSettings()` and `applySettings(...)`,
and `tests/configuration/sales/checkout.spec.ts` captures the originals in
`beforeEach` and puts them back in `afterEach`:

```ts
let original: CheckoutSettings;

test.beforeEach(async ({ adminPage }) => {
    configPage = new CheckoutConfigurationPage(adminPage);
    original = await configPage.readSettings();
});

test.afterEach(async () => {
    await configPage.applySettings(original);
});
```

If a test changes a global setting:

1. **Read** the current value first, or know the default from
   `packages/Webkul/Admin/src/Config/system.php`.
2. **Set** it to the value the test needs — idempotently, never by clicking a
   toggle blind.
3. Change it, and assert the behaviour it was supposed to change, not just that
   the save toast appeared.
4. **Restore** the original in `afterEach`, in a `finally`, so a failed assertion
   still restores.

[admin-and-shop.md](admin-and-shop.md) has the set-don't-toggle mechanics, the
in-repo page object that already does it correctly, and the map of which
configuration areas other specs silently depend on. The same ownership applies to
anything else global: a channel's default locale, a currency's exchange rate, an
inventory source, a theme's published sections.

## Cleanup

`afterEach` runs against a database that keeps everything the test made. Two
rules:

- **Never let one cleanup step's failure skip the next.** Delete the product in
  a `finally`, so a missing rule cannot strand it.
- **Tolerate what the test never created.** When a test fails before creating
  its rule, the delete control is absent; wait briefly and return rather than
  timing out and aborting the rest of the teardown.

```ts
async deleteCatalogRuleAndProduct(ruleName: string, sku: string) {
    try {
        await this.deleteRuleIfPresent(ruleName);
    } finally {
        await this.deleteProductBySku(sku);
    }
}
```

Cleanup must be **scoped to what the test created** — by name, by SKU, by email.
A teardown that deletes `.icon-delete` `.first()`, or ticks the checkbox at
`.nth(2)`, removes whatever happens to occupy that position — someone else's row
on a shared dev database. Search for the record the test named, then delete that
row.

Not everything has to be deleted. A record with a unique generated name that no
other test looks for is often better left than removed by a fragile teardown —
the cost is a growing dev database, and the alternative cost is a teardown that
deletes the wrong row. Delete when the record would otherwise be found by a
later search, when it changes a count the UI shows, or when it holds a unique
value another test needs.

## Test independence

Every spec must pass when run alone:

```bash
npm run test:e2e -- tests/customers/customers.spec.ts -g "should edit customer"
```

`workers: 1` and file-order execution are an implementation detail, not a
contract. A test may not rely on:

- another spec having created a record;
- a spec in the *other* suite having run — the Admin and Shop projects are
  launched separately, so a Shop test may never assume an Admin spec configured
  anything ([admin-and-shop.md](admin-and-shop.md));
- an earlier test in the same file having left state (beyond a read-only
  `beforeAll` fixture);
- the order tests happen to be declared in;
- a browser context another test logged in;
- seeded data that a previous run mutated.

The shape to avoid — and it is in the suite today:

```
test A creates a customer
test B opens "the first customer" and edits it
test C deletes an address from "the first customer"
```

Each of B and C must create the customer it needs, or take it from a
`beforeEach` that creates one per test.

## When may a test go around the UI

The behaviour under test is exercised through the browser, always. A test of
"the admin can create a customer" that posts to the API and then asserts a row
has tested the API, not the screen.

Going around the UI is acceptable for **setup and teardown only**, and even then
these suites do not currently do it — there is no API client or database access
layer under `tests/e2e-pw/`, and prerequisites are created by driving the admin
UI through page objects such as `ProductCreatePage`. Follow that. Introducing a
direct API or database path is a real addition to the architecture: justify it
by cost (a checkout spec that needs six products), keep it strictly to
preconditions, and never use it to assert an outcome that the user is supposed
to be able to see.

Never assert on the database in place of asserting on the screen. If the user
cannot see it, an E2E test is the wrong place to prove it — see
[test-design.md](test-design.md).
