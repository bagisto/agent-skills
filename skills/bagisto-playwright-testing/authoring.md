# Authoring a spec and its page object

## Contents

- [Layout](#layout)
- [The page object](#the-page-object)
- [Fixtures](#fixtures)
- [Test data](#test-data)
- [ACL specs](#acl-specs)
- [Naming](#naming)

## Layout

A feature needs two files: a spec that states intent, and a page object that
owns every locator.

```
tests/e2e-pw/
├── tests/<section>/<feature>.spec.ts        # what should happen
└── pages/admin/<section>/<Feature>Page.ts   # how to drive it
```

`tests/` mirrors the admin menu (`catalog/`, `customers/`, `marketing/`,
`settings/`, `appearance/`). Put a new spec where its menu section sits, so the
shard split stays even and the file is findable from the UI.

Note one existing exception: every ACL spec lives in `tests/settings/acl/`,
including `catalog-acl.spec.ts` and `cms-acl.spec.ts`, which cover other
sections. Follow that, not the menu, for ACL.

## The page object

Extend `BasePage`, which supplies `visit()` (relative to the configured base
URL) and `dataPath()` (files under `tests/e2e-pw/data`). Resolve paths through
`utils/paths.ts` rather than walking up from `__dirname`.

```ts
import { expect, type Page } from "@playwright/test";
import { BasePage } from "../../BasePage";
import { generateName } from "../../../utils/faker";

export class SectionsPage extends BasePage {
    constructor(page: Page) {
        super(page);
    }

    private get createButton() {
        return this.page.getByTitle("Create Section");
    }

    private sectionRow(name: string) {
        return this.page
            .locator("div[data-draggable]")
            .filter({ hasText: name });
    }

    async open(): Promise<void> {
        await this.visit("admin/appearance/themes/default/sections");
        await this.page.waitForLoadState("networkidle");
        await expect(this.createButton).toBeVisible();
    }

    async createSection(type: string): Promise<string> {
        const name = generateName();
        // …drive the UI, assert the outcome…
        return name;
    }
}
```

Rules that hold across the existing suite:

- **Locators are private getters or private methods.** A spec never contains a
  selector. A locator that takes an argument (a row by name, a field by label)
  is a private method, not a getter. A locator a subclass needs is
  `protected`, never public — `CheckoutHelper` is the base every product-type
  checkout extends, so its locators are protected and only its actions
  (`searchProduct`, `checkoutWithNewAddress`) stay public. No locator is ever
  public.
- **Member order: fields and constructor, then getters, then private locator
  methods, then private helpers, then public actions.** A private helper wedged
  between two public methods is the same defect the
  `bagisto-package-development` skill names for PHP classes.
- **Public methods are named for the user's intent** — `createSection`,
  `deleteSection`, `expectFooterLinksNotOffered` — and assert their own outcome.
  A method that only clicks and returns pushes the assertion into the spec,
  where the locator is not available.
- **Return what the caller needs to assert on**, usually the generated name.
- **No comments, anywhere under `tests/e2e-pw/`** — not a `//` line, not a
  `/* */` block, not a docblock, in a spec or a page object. When a step needs
  prose to be understood, that is the signal to extract a method whose name
  carries the reason: `deleteRuleIfPresent`, not `deleteFirstRule` plus a
  sentence explaining that it skips when none exists.

An assertion is the usual thing a spec reaches a locator for. Give the page
object the assertion instead:

```ts
// the spec holds a selector, and `visit` is protected
await ruleApplyPage.searchInput.fill(product.name);
await expect(ruleApplyPage.addToCartSuccessMessage).toBeVisible();

// the page object owns both, and the spec reads as intent
const subtotal = await ruleApplyPage.addSavedProductToCart(qty);
await ruleApplyPage.expectGrandTotal(expected);
```

## Fixtures

`setup.ts` exports `test` with two fixtures. Import from there, never from
`@playwright/test` directly, or you lose them:

```ts
import { test } from "../../setup";
```

| Fixture | Gives you |
|---|---|
| `adminPage` | A page already logged into admin, via cached `storageState`, re-logging in if the session expired. Also `fillInTinymce(iframeSelector, content)`. |
| `shopPage` | A fresh storefront context, no auth. Also `fillInTinymce`. |

Never call the login flow yourself in a spec — `adminPage` has done it.

## Test data

Use `utils/faker.ts` rather than literals, so parallel shards and repeat runs do
not collide: `generateName`, `generateEmail`, `generateSKU`, `generateSlug`,
`generateDescription`, `getImageFile`, and others.

A generated name is also what makes a row-scoped assertion possible — it is
unique, so `filter({ hasText: name })` resolves to exactly one row.

**Generate the value inside `beforeEach`, never at module scope.** A module-scope
initialiser runs once per file, so every test in that file reuses one SKU or
name. `sku` is `Rule::unique` and `url_key` is validated by
`ProductCategoryUniqueSlug`, so the second test 422s with "The sku has already
been taken" the moment cleanup misses once — and since its own cleanup then
fails too, every remaining test in the file fails with it. This is the single
most common cause of a spec file that passes alone and fails in a suite.

```ts
let generatedSku: string;                    // declare at module scope

test.beforeEach(async ({ adminPage }) => {
    generatedSku = `SKU-${Date.now()}`;      // assign per test
});
```

If a module-scope table needs the value, hold it as a thunk — the table is built
at import time, when the variable is still undefined:

```ts
const testCases = [{ operator: "==", value: () => generatedSku }];
// at the call site
value: testCase.value(),
```

Prefer `Date.now()` over `generateSKU()` where uniqueness must hold across
reruns: `generateSKU()` is random (`AAA1234`), and the suite never rolls back,
so a collision with an earlier run's leftover row is possible.

Binary fixtures live in `tests/e2e-pw/data/` and are reached with
`this.dataPath("file.png")`.

## Cleanup

`afterEach` runs against a database that keeps everything the test made, so a
leaked row poisons whatever runs next. Two rules:

- **Never let one cleanup step's failure skip the next.** Delete the product in
  a `finally`, so a missing rule cannot strand it.
- **Tolerate what the test never created.** When a test fails before creating
  its rule, the delete icon is absent; wait briefly and return rather than
  timing out and aborting the rest of the teardown.

```ts
async deleteCatalogRuleAndProduct() {
    try {
        await this.deleteRuleIfPresent(path, "Catalog Rule Deleted Successfully");
    } finally {
        await this.deleteLatestProduct();
    }
}
```

Positional cleanup (`.first()`, `.nth(2)`) is a standing hazard: it deletes
whatever currently sits in that row, not what this test created. It only works
while nothing else writes to the same grid.

## ACL specs

ACL coverage is data-driven rather than hand-written per role. `pages/admin/acl/`
holds a class chain (`shared.ts` → per-section files → `index.ts` exporting
`ACLManagement`) plus `routes.ts`, a map from a permission key to what that role
may and may not reach:

```ts
"appearance->themes": {
    allowed: "admin/appearance/themes",
    sidebar: "/admin/appearance/themes",
    notAllowed: [
        "admin/appearance/themes/default/sections",
        "admin/dashboard",
        // …
    ],
},
```

A spec then creates the role, creates a user, and verifies:

```ts
const aclManagement = new ACLManagement(adminPage);
await aclManagement.createRole("custom", ["appearance"]);
await aclManagement.editRolePermission(["appearance.sections"]);  // untick siblings
await aclManagement.createUser();
await aclManagement.verfiyAssignedRole(["appearance->themes"]);
```

Notes that catch people out:

- **Ticking a parent permission ticks every descendant**, and ticking a child
  ticks its ancestors. `editRolePermission([...])` **unticks** the keys passed,
  which is how a single-permission role is produced.
- **`sidebar` is optional.** A page reached from inside another screen has no
  menu entry, so omit it rather than asserting a link that cannot exist.
- **Permissions are exact-match**, not prefix-match: holding `appearance` alone
  grants neither `appearance.themes` nor `appearance.sections`. Verify what a
  role actually opens before asserting it.
- `verfiyAssignedRole` is spelled that way in the codebase. Match it.

## Naming

- Spec file: `<feature>.spec.ts`, **lower-kebab** — `buy-x-get-y-free.spec.ts`,
  `url-key.spec.ts`, `price-in-cart.spec.ts`. Not camelCase (`urlKey.spec.ts`),
  not run-together (`buyXgetYfree.spec.ts`), and no stray dot inside the stem
  (`price-in.cart.spec.ts`).
- **A file that declares a class is named for that class, exactly.** Page
  objects are `<Feature>Page.ts` holding `class <Feature>Page`, and the rule
  holds everywhere — `CatalogAclPage.ts` not `catalog.ts`, `ACLManagement.ts`
  not `index.ts`, `TinymcePage.ts` not `tinymce.ts`. When the two disagree,
  rename whichever is wrong: the file when the class name is good, the class
  when it is not (`ProductCreatePage.ts` exporting `ProductCreation` is the
  class's fault). Match the casing a sibling already set — `RmaCreatePage`
  beside `RmaManagePage`, not `RMACreatePage`.
- A module with no class keeps its lower-kebab name: `utils/faker.ts`,
  `utils/paths.ts`, `*.types.ts`. If a file holds one dead class and one live
  function, delete the class rather than rename the file around it.
- Directories: lower-kebab, mirroring the admin menu section.
- `test.describe("<feature> management")`, matching the existing suite.
- **Describe blocks and test titles are lower case throughout**, including
  acronyms and brand names, because that is what the suite already does — `rma`,
  `gdpr`, `sku`, `url`, `cms`, `seo`, `pdf`, `github`. Trim leading and trailing
  spaces, never double-space, and write an arrow with one space each side:
  `condition is -> is equal to`, not `is->is equal to`.
- Test title: `should <expected outcome>` — describe the behaviour, not the
  mechanism. `should stage a reorder until it is published`, not
  `should call the reorder endpoint`.
