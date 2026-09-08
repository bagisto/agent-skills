# Investigating before writing

## Contents

- [What investigation produces](#what-investigation-produces)
- [1. Understand the feature from the application code](#1-understand-the-feature-from-the-application-code)
- [2. Find the validation and business rules](#2-find-the-validation-and-business-rules)
- [3. Find the exact UI strings](#3-find-the-exact-ui-strings)
- [4. Map the feature's impact surface](#4-map-the-features-impact-surface)
- [5. Inspect the existing tests](#5-inspect-the-existing-tests)
- [6. Read existing tests critically](#6-read-existing-tests-critically)
- [7. Inspect existing page objects, fixtures and helpers](#7-inspect-existing-page-objects-fixtures-and-helpers)
- [8. Identify the user workflows](#8-identify-the-user-workflows)

## What investigation produces

Before any code, you should be able to state, in a few lines:

- what the feature does, and which routes and controllers implement it;
- what the validation and business rules are, including the ones the UI never
  shows;
- what it touches — the impact surface, and which side of the app the outcome is
  visible on;
- which existing specs already touch it, and what each of them actually proves;
- which page objects, fixtures and helpers already drive it;
- the user workflows worth covering, and what each one requires to exist first.

If you cannot write those lines, you cannot yet judge whether a test is
worth adding — you can only guess. Write them into your working notes or your
reply; they are what makes the scenario matrix in
[test-design.md](test-design.md) an informed one.

**The UI is not the specification.** Bagisto puts a great deal of behaviour
where the browser never shows it: `Rule::unique` on a SKU, a channel/locale
dimension on an attribute value, an ACL key that gates a route, a config default
that changes a storefront layout. Reading the code is how you find the
behaviours that are worth a test and the ones a browser cannot see.

## 1. Understand the feature from the application code

Work from the URL inwards. For an admin screen at
`admin/customers/customers`:

```bash
grep -rn "customers/customers" packages/Webkul/Admin/src/Routes/
grep -rn "class CustomerController" packages/Webkul/Admin/src/Http/Controllers/Customers/
```

| Looking for | Where it lives |
|---|---|
| The route name and its middleware | `packages/Webkul/<Pkg>/src/Routes/*-routes.php` |
| The action, and what it returns on success or failure | `src/Http/Controllers/{Admin,Shop}/…` |
| The persisted shape and its mutators | `src/Models/`, `src/Contracts/` |
| The query behind a listing | `src/DataGrids/…` (`prepareQueryBuilder`) |
| The rendered markup and its Vue components | `src/Resources/views/…` |
| Admin settings that change behaviour | `packages/Webkul/Admin/src/Config/system.php` |
| The permission key that gates the screen | `packages/Webkul/Admin/src/Config/acl.php` |

The DataGrid class is worth a special look for any listing feature: it tells you
which columns are searchable, which filters exist, and what a mass action really
does — none of which is discoverable by clicking.

## 2. Find the validation and business rules

Three places, in order:

```bash
ls packages/Webkul/Admin/src/Http/Requests/          # FormRequest classes
grep -rn "validate(\[" packages/Webkul/<Pkg>/src/Http/Controllers/
grep -rn "public function rules" packages/Webkul/<Pkg>/src/
```

Then read the repository or model for the rules the request does not carry —
mutators that turn `''` into `null`, `$casts`, events fired on create or update,
and anything in an `AbstractType` for product behaviour.

What you are looking for, specifically:

- **Required fields** — candidates for a validation scenario.
- **Uniqueness** (`Rule::unique`, `ProductCategoryUniqueSlug`) — these are the
  rules a shared, never-rolled-back database will trip over, and they dictate
  the test data strategy in [test-data.md](test-data.md).
- **Boundaries** — numeric ranges, string lengths, date ordering.
- **State transitions** — an order that cannot go from cancelled to shipped, a
  section change that is staged until published.
- **Conditional behaviour** — a rule that only applies when a config flag is on,
  a field that only appears for one product type.

Each of these is a candidate scenario. Not all of them belong in Playwright —
[test-design.md](test-design.md) decides that.

## 3. Find the exact UI strings

Assertions match on translated text, so the string in the lang file is the
contract, not the string you remember from the UI.

```bash
grep -rn "create-success" packages/Webkul/Admin/src/Resources/lang/en/app.php
```

`'create-success' => 'Customer created successfully'` — note there is no full
stop, while many Shop-side messages have one. Guessing costs a failing run;
grepping costs a second. Where a message is assembled from a partial match,
assert on the distinctive fragment rather than the whole sentence.

## 4. Map the feature's impact surface

Coverage decisions need to know what the feature touches, not just what it is.
Walk the surface once and write down what applies — most features touch four or
five of these, not all of them:

| Dimension | Ask |
|---|---|
| Admin UI | Which screens create, edit, list or configure it? |
| Shop UI | What does the customer see change, and where? |
| Model / repository / service | What is persisted, and what derives from it? |
| Routes and controllers | Which endpoints, and what do they return on refusal? |
| Events and listeners | What fires on create, update or delete, and what listens? |
| Configuration | Which `system.php` keys change its behaviour? |
| Permissions | Which `acl.php` key gates it? |
| Catalog data | Attributes, families, categories, product types, inventory |
| Commerce flow | Pricing, cart, checkout, orders, customer account |

Then answer five questions. These, not the list above, are what drive coverage:

1. **What is the source of truth?** The place a change must land for the feature
   to be correct — a column, a config value, a pivot row.
2. **Which roles are affected?** Guest, customer, admin, admin without the
   permission.
3. **Which existing behaviour could regress?** What used to work that this
   change routes through.
4. **What configuration and data must exist** for the behaviour to be reachable
   at all?
5. **What downstream customer-visible behaviour changes?** An admin-only change
   with a storefront consequence needs coverage on both sides —
   see [admin-and-shop.md](admin-and-shop.md).

**Do not test every affected component through the browser.** The surface map
tells you where the risk is; [test-design.md](test-design.md) decides which of it
earns an E2E test and which belongs in Pest. A feature that touches eight
dimensions may still deserve three Playwright tests.

## 5. Inspect the existing tests

```bash
grep -rln "customer" packages/Webkul/Admin/tests/e2e-pw/tests/
grep -rn "test(" packages/Webkul/Admin/tests/e2e-pw/tests/customers/customers.spec.ts
grep -rn "CustomersPage" packages/Webkul/*/tests/e2e-pw/
```

Also check the Pest side, because a behaviour already proven there may not need
a browser at all:

```bash
grep -rln "Customer" packages/Webkul/Admin/tests/Feature/
```

Then answer explicitly: **does an existing test already prove the behaviour I
was asked to cover?** If it does, the work is to strengthen, extend or
parameterise that test, not to add a second one beside it. Two tests asserting
the same guarantee cost twice the maintenance and give no extra confidence.

Entering the same behaviour through a different UI path is not, on its own, a
new scenario. A customer created from the customer grid and one created from the
order-creation drawer are two tests only if the two paths run different code —
different requests, different validation, different defaults. Check before
assuming either way.

## 6. Read existing tests critically

Never treat an existing test as correct because it passes, and never copy its
pattern before deciding what it proves.

Ask of any test you are about to reuse or extend:

| Question | What a bad answer looks like |
|---|---|
| Does it assert the outcome, or only that nothing threw? | A domain action called with no assertion in the spec body |
| Could it pass with the feature broken? | Asserting only "Configuration saved successfully" — the toast appears whether or not the value persisted |
| Does it depend on seeded or leftover data? | Acting on a seeded product by name, or on "the first customer" |
| Does it depend on another test having run? | A test that edits a record an earlier `test()` created |
| Does it depend on file order? | Anything that reads a row index rather than searching for its own record |
| Are the locators stable? | `.icon-uncheckbox` `.nth(2)`, `div.border-b`, `button.primary-button:visible` |
| Does it contain arbitrary waits? | Any `waitForTimeout` — there are none left in the suites |
| Does it test implementation detail? | Asserting on a Vue wrapper class rather than on what the user sees |
| Does it change global state without restoring it? | Changing a `tests/configuration/**` setting and leaving it |

These are the shapes the suite cleanup removed, which is why most of them no
longer have an in-repo example. They come back easily; the column describes what
to refuse in review, not what you will find today.

When the pattern you were going to copy fails one of these, fix it rather than
reproducing it. Improving a weak test that already covers your behaviour is
almost always better work than adding a strong test next to it.

## 7. Inspect existing page objects, fixtures and helpers

**Reuse → extend → refactor → create new.** Search before building anything:

```bash
ls packages/Webkul/Admin/tests/e2e-pw/pages/admin/<section>/
grep -rn "class .*Page" packages/Webkul/Admin/tests/e2e-pw/pages/ | grep -i <feature>
grep -rn "export function" packages/Webkul/Admin/tests/e2e-pw/utils/
```

What already exists:

| Kind | Shared (`@shared/*`) | Admin | Shop |
|---|---|---|---|
| Fixtures | — | `adminPage`, `shopPage`, `fillInTinymce` (`setup.ts`) | same |
| Login | — | `utils/admin.ts` → `loginAsAdmin` | `utils/admin.ts`, `utils/customer.ts` → `register`, `loginAsCustomer` |
| Data generation | `faker.ts` | `utils/faker.ts` re-exports it, adds `generateSKU`, `generateFullName`, `generateCurrencyCode`, `getImageFile` | `utils/faker.ts` re-exports it, adds `generateLocation` |
| Environment | `env.ts` | `utils/env.ts` (adds `dotenv`) | same |
| Paths | `paths.ts` | `utils/paths.ts` → `DATA_PATH`, `ADMIN_AUTH_STATE_PATH` | same |
| Prices | `prices.ts` | via `utils/tax.ts` | `utils/prices.ts` |
| Regex | `regex.ts` | imported directly by page objects | same |
| Listings | — | `pages/admin/DatagridPage.ts` base class | — |
| Product setup | — | `pages/admin/catalog/products/ProductCreatePage.ts` | its own copy, plus `pages/types/product.types.ts` |
| Domain helpers | — | `utils/configuration.ts`, `tax.ts`, `numbers.ts`, `customer.ts` | `utils/TinymcePage.ts` |
| CSV / import fixtures | — | `utils/csv.ts`, `customers-csv.ts`, `products-csv.ts`, `tax-rates-csv.ts`, `data-transfer.ts` | — |

Two things to keep straight:

- **The suites share the dependency-free helper layer and nothing else.**
  `@shared/*` is real and used; page objects, fixtures and specs are not shared,
  and `ProductCreatePage` genuinely exists twice. Never import a page object or
  a Playwright-dependent util across the package boundary — extend the copy in
  the suite you are in, and if both need it, change both.
- **New shared code must be dependency-free** or it breaks CI, which installs
  `node_modules` per package only. See [SKILL.md](SKILL.md).

The `tsconfig.json` aliases `@pages/*`, `@utils/*` and `@data/*` are declared but
unused — every intra-suite import is relative. `@shared/*` is the exception and
is the one you should use. Match the suite.

## 8. Identify the user workflows

A workflow is a thing a person is trying to achieve, not a screen. "Create a
cart rule" is a workflow; "the cart rule form" is not.

For each workflow, name three things:

1. **The entry point** — where the user starts, and what must already exist.
2. **The observable outcome** — what changes on screen, and what changes that
   the user can go back and see later.
3. **The failure modes** — what the application refuses to do, and how it says so.

The third is what most weak tests skip, and it is usually where the interesting
coverage lives. A create flow with no test of what happens on a duplicate SKU
has covered the easy half.

Take the list of workflows into [test-design.md](test-design.md).
