# Authoring a spec and its page object

## Contents

- [Layout](#layout)
- [What goes in the spec, what goes in the page object](#what-goes-in-the-spec-what-goes-in-the-page-object)
- [The page object](#the-page-object)
- [Fixtures](#fixtures)
- [ACL specs](#acl-specs)
- [Naming](#naming)
- [The no-comments rule](#the-no-comments-rule)

## Layout

A feature needs two files: a spec that states intent, and a page object that
owns every locator.

```
tests/e2e-pw/
├── tests/<section>/<feature>.spec.ts        # what should happen
└── pages/admin/<section>/<Feature>Page.ts   # how to drive it
```

The Admin suite's `tests/` mirrors the admin menu; the Shop suite's mirrors the
customer journey. Which suite a test belongs in, where inside it, and why
filenames never carry an execution order, are all in
[admin-and-shop.md](admin-and-shop.md).

A spec that runs longer than its suite's per-test budget declares it itself —
`test.setTimeout(240000)` inside the describe, as the tax and omnibus specs do.
Raise the budget for the one flow that needs it; never in the config.

## What goes in the spec, what goes in the page object

The spec composes a workflow out of named intentions and states the guarantee.
The page object knows the UI. Getting this boundary right is what makes a test
survive a redesign.

```ts
test("should reject a duplicate sku", async ({ adminPage }) => {
    const productPage = new ProductCreatePage(adminPage);
    const sku = `SKU-${uniqueStamp()}`;

    await productPage.createProduct({ type: "simple", sku, ...rest });

    await productPage.attemptCreateProduct({ type: "simple", sku, ...rest });

    await productPage.expectSkuRejectedAsDuplicate();
    await productPage.expectProductCountForSku(sku, 1);
});
```

Three levels, and each has a job:

| Level | Example | Owns |
|---|---|---|
| Domain action | `createProduct(data)`, `searchProduct(name)`, `deleteCategory(name)` | Driving the UI, plus asserting that the action itself succeeded |
| Assertion method | `expectGrandTotal(amount)`, `expectRowListed(name)`, `expectFooterLinksNotOffered()` | One user-visible fact |
| Spec | the `test()` body | Which actions, in what order, and which facts are the guarantee |

**Avoid whole-scenario page-object methods.** A method like
`discardRevertsStagedStatus()` or `createProductAndVerifySuccessfully()` leaves
the spec body a single call, so the test title is the only description of the
behaviour, nothing can be varied, and the assertions are invisible at the point
where someone reads the test. Do not add methods shaped like that.

A whole test hidden behind one call:

```ts
await sectionsPage.discardRevertsStagedStatus();
```

The same test, composed from actions and assertion methods:

```ts
const name = await sectionsPage.createSection("Static Content");

await sectionsPage.publishAll();
await sectionsPage.toggleStatus(name);
await sectionsPage.expectChangeStaged(name);

await sectionsPage.discardAll();
await sectionsPage.expectNoStagedChange(name);
await sectionsPage.expectSectionEnabled(name);
```

The second form reads as the behaviour it guarantees, and the next test can
reuse `toggleStatus` without inheriting someone else's assertions.

**But do not shred the workflow into clicks either.** `clickName()`,
`fillName()`, `clickSave()`, `clickConfirm()` in the spec is the same defect
from the other side: the spec now describes mechanism, and a form change touches
every test. If a sequence of steps is one thing a user does, it is one method.

The test to apply: *could a reader of the spec say what behaviour is guaranteed,
without opening the page object?* If not, the abstraction is at the wrong level.

## The page object

Extend `BasePage`, which supplies `visit()` (relative to the configured base
URL) plus `waitForVueMount()` and `waitForBackgroundRequestsToSettle()`. Reach
fixture files through `DATA_PATH` from `utils/paths.ts` —
see [test-data.md](test-data.md).

```ts
import { expect, type Page } from "@playwright/test";
import { BasePage } from "../../BasePage";
import { generateName } from "../../../utils/faker";

export class CategoryPage extends BasePage {
    constructor(page: Page) {
        super(page);
    }

    private get createButton() {
        return this.page.getByRole("button", { name: "Create Category" });
    }

    private get createForm() {
        return this.page.locator("#category-create-form");
    }

    private get saveButton() {
        return this.page.getByRole("button", { name: "Save Category" });
    }

    private row(text: string) {
        return this.page
            .locator("div.row:not(.datagrid-head)")
            .filter({ hasText: text });
    }

    private async openCreateForm(): Promise<void> {
        await this.createButton.click();
        await this.createForm.waitFor();
    }

    async open(): Promise<void> {
        await this.visit("admin/catalog/categories");

        await expect(this.createButton).toBeVisible();
    }

    async createCategory(): Promise<string> {
        const name = generateName();

        await this.open();
        await this.openCreateForm();
        await this.createForm.locator('input[name="name"]').fill(name);
        await this.saveButton.click();

        await expect(
            this.page.getByText("Category created successfully"),
        ).toBeVisible();

        return name;
    }

    async expectCategoryListed(name: string): Promise<void> {
        await this.open();

        await expect(this.row(name)).toHaveCount(1);
    }
}
```

The selectors above are illustrative — confirm each against the real Blade
before using it.

Rules that hold across the existing suite:

- **Locators are private getters or private methods.** A spec never contains a
  selector. A locator that takes an argument (a row by name, a field by label)
  is a private method, not a getter. A locator a subclass needs is `protected`,
  never public — `CheckoutHelper` is the base every product-type checkout
  extends, so its locators are protected and only its actions
  (`searchProduct`, `checkoutWithNewAddress`) stay public. No locator is ever
  public.
- **Member order: fields and constructor, then getters, then private locator
  methods, then private helpers, then public actions, then public `expect…`
  methods.** A private helper wedged between two public methods is the same
  defect the `bagisto-package-development` skill names for PHP classes.
- **Public methods are named for the user's intent**, and a domain action
  asserts that it itself succeeded — `createCategory` above waits for the
  success message before returning. A method that only clicks and returns pushes
  the assertion into the spec, where the locator is not available. Keep that
  assertion to *the action worked*; the behaviour the test is about belongs in
  an `expect…` method the spec calls.
- **Return what the caller needs to assert on**, usually the generated name.
- **A page object never reaches into another page object's locators.** If two
  screens share a control, the shared base owns it as `protected`.

## Fixtures

`setup.ts` exports `test` with two fixtures. Import from there, never from
`@playwright/test` directly, or you lose them:

```ts
import { test, expect } from "../../setup";
```

| Fixture | Gives you |
|---|---|
| `adminPage` | A page already logged into admin, via cached `storageState`, re-logging in if the session expired. Also `fillInTinymce(iframeSelector, content)`. |
| `shopPage` | A fresh storefront context, no auth. Also `fillInTinymce`. |
| `page` | Playwright's own fixture — a bare context with neither. |

Rules:

- **Never call the login flow yourself in a spec.** `adminPage` has done it, and
  a hand-rolled login costs a page load per test.
- **One context, both halves.** A spec that sets something up in admin and then
  verifies it on the storefront can do both on `adminPage`: an admin session
  does not make the storefront non-guest. A handful of Shop specs still take the
  bare `page` fixture and call `loginAsAdmin(page)` by hand — that form is
  legacy; do not extend it, and moving one to `adminPage` while you are in the
  file for another reason is a welcome cleanup.
- **A customer session needs `shopPage`** plus `register` / `loginAsCustomer`
  from `utils/customer.ts` — do not mix a customer login into `adminPage`.
- **`fillInTinymce` behaves the same in both suites**: it resolves the editor by
  id, waits for `editor.initialized`, calls `setContent` and asserts the frame
  body took the text. Admin defines it inline in `setup.ts`; Shop keeps it in
  `utils/TinymcePage.ts`. Use the one in your suite rather than importing across
  packages.

## ACL specs

ACL coverage is data-driven rather than hand-written per role.
`pages/admin/acl/` holds two files:

- **`routes.ts`** — the data. `MODULE_PROBES` maps a top-level module to a
  representative URL, and `MODULE_ROUTES` declares, per permission key, the route
  it grants (`allowed`), the sidebar href it should show (`sidebar`, optional)
  and, derived from the probes, the routes it must *not* reach (`denied`).
- **`RestrictedAdminPage.ts`** — the driver. It logs in as the restricted user
  and exposes four assertions: `expectRouteAllowed`, `expectRouteDenied`,
  `expectSidebarLinkVisible` and `expectSidebarLinkAbsent`.

The specs are `tests/settings/acl/role-permissions.spec.ts` (which routes a role
opens) and `role-action-permissions.spec.ts` (what it may do once inside). Both
build the role and user through the settings page objects, then drive
`RestrictedAdminPage` over the table.

Adding coverage usually means **adding a row to `routes.ts`**, not writing a new
spec. Notes that catch people out:

- **Start from `packages/Webkul/Admin/src/Config/acl.php`.** The keys and the
  routes each key gates are declared there; `routes.ts` must agree with it. A
  new admin screen usually means a new entry in both.
- **Ticking a parent permission ticks every descendant**, and ticking a child
  ticks its ancestors. Producing a single-permission role therefore means
  unticking the rest, not ticking one box.
- **`sidebar` is optional.** A page reached from inside another screen has no
  menu entry, so omit it rather than asserting a link that cannot exist.
- **Permissions are exact-match**, not prefix-match: holding `appearance` alone
  grants neither `appearance.themes` nor `appearance.sections`. Verify what a
  role actually opens before asserting it.
- **A `denied` entry must prove refusal, not absence.** `expectRouteDenied`
  asserts the denial the application actually shows, so the test cannot pass
  because the page merely failed to load.

## Naming

- Spec file: `<feature>.spec.ts`, **lower-kebab** — `buy-x-get-y-free.spec.ts`,
  `url-key.spec.ts`, `price-in-cart.spec.ts`. Not camelCase (`urlKey.spec.ts`),
  not run-together (`buyXgetYfree.spec.ts`), and no stray dot inside the stem
  (`price-in.cart.spec.ts`).
- **A file that declares a class is named for that class, exactly.** Page
  objects are `<Feature>Page.ts` holding `class <Feature>Page`, and the rule
  holds everywhere — `RestrictedAdminPage.ts` not `acl.ts`, `DatagridPage.ts`
  not `grid.ts`, `TinymcePage.ts` not `tinymce.ts`. When the two disagree,
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
- **The title states the behavioural guarantee**, in the form
  `should <expected outcome>`. It should be possible to read the title and know
  what breaks if the test goes red.

  | Avoid | Prefer |
  |---|---|
  | `should work` | `should keep the cart total after a page reload` |
  | `should create` | `should list a newly created category in the grid` |
  | `validation test` | `should reject a product whose sku already exists` |
  | `should call the reorder endpoint` | `should stage a reorder until it is published` |

  Fix a spelling mistake in a title you are already editing.

## The no-comments rule

**No comments anywhere under `tests/e2e-pw/`** — not a `//` line, not a `/* */`
block, not a docblock, in a spec or a page object. This is a Bagisto convention
and it is held: all three suites contain zero comments today.

It diverges from generic Playwright guidance, which permits a comment for a
non-obvious workaround, a browser limitation, unusual application behaviour, or
a business constraint. Bagisto covers those cases with names instead:

| Generic advice would comment | Bagisto encodes it as |
|---|---|
| "skip when no rule exists" | `deleteRuleIfPresent(...)`, not `deleteFirstRule` plus a sentence |
| "drag events, `dragTo` is unreliable here" | a private `dragRowOnto(from, to)` whose body is the workaround |
| "the drawer covers the list" | `closeOpenSection()` called before acting on the list |
| "3000 ms because the indexer is slow" | a wait on the state that the indexer produces — see [locators.md](locators.md) |

If a step still cannot be understood without prose after naming it, that is a
signal the method is doing two things, not that the file needs a comment.
