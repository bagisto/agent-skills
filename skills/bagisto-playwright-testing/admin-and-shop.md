# Admin and Shop: responsibilities, prerequisites, organisation

## Contents

- [Two suites, two responsibilities](#two-suites-two-responsibilities)
- [Which suite does a test belong in](#which-suite-does-a-test-belong-in)
- [A business prerequisite is not an execution dependency](#a-business-prerequisite-is-not-an-execution-dependency)
  - [Pass data explicitly, never through disk or module state](#pass-data-explicitly-never-through-disk-or-module-state)
- [Establishing an admin prerequisite from a Shop test](#establishing-an-admin-prerequisite-from-a-shop-test)
- [Set, never toggle](#set-never-toggle)
- [The global configuration surface](#the-global-configuration-surface)
- [A worked example](#a-worked-example)
- [Organising each suite](#organising-each-suite)

## Two suites, two responsibilities

| | Admin suite | Shop suite |
|---|---|---|
| Proves | the administrator can configure, create and manage the capability | the customer actually experiences the configured behaviour |
| Actor | an admin user, with or without a permission | a guest, or a logged-in customer |
| Typical assertion | the record exists in the grid with the entered data; the setting saved and reads back | the storefront shows the price, the cart totals, the order is placed |
| Owns | admin CRUD, configuration screens, ACL, admin-side workflows | catalog browsing, cart, checkout, customer account, orders, reviews, wishlist |

Two tests of "guest checkout" are therefore two different guarantees, and both
are worth having:

- **Admin:** the guest-checkout setting can be turned on, saves, and reads back
  as on.
- **Shop:** with guest checkout on, a guest can complete an order and sees the
  confirmation; with it off, checkout requires sign-in.

The Admin test proves the switch moves. The Shop test proves the switch is wired
to anything. Neither substitutes for the other.

## Which suite does a test belong in

**Put the test where the outcome it verifies is visible.** If the assertion is on
a storefront page, the test belongs in the Shop suite even when most of its setup
happens in admin.

Bagisto does not hold this uniformly, and both shapes exist on purpose:

- The promotion specs live in the **Shop** suite (`Shop/tests/promotion/…`) and
  reach into admin through `Shop/tests/e2e-pw/pages/admin/` to create the rule.
  The outcome — a discounted grand total at checkout — is customer-visible.
- The omnibus pair lives in the **Admin** suite, keeping
  `omnibus-admin.spec.ts` and `omnibus-shop.spec.ts` beside each other, which is
  why `Admin/tests/e2e-pw/pages/shop/` exists.

Either home is defensible. What is not defensible in either is a test that needs
the *other suite's spec* to have run. Follow the placement of the feature you are
extending; for genuinely new coverage, use the outcome rule.

**Each suite owns page objects for whatever screens it needs to drive**,
including the other side's. That is the mechanism that keeps the suites
independent — not a smell to be cleaned up.

## A business prerequisite is not an execution dependency

This is the rule that matters most in Bagisto, because the domain is full of
real dependency chains:

```
attributes → attribute families → categories → products → cart → checkout → orders
```

Those chains are true of the *business*. They must never become true of the
*test run*.

| Legitimate | Illegitimate |
|---|---|
| A checkout test creates, in a hook, the product it will buy | A checkout test buys whatever product an earlier `test()` in the file created |
| A Shop test enables guest checkout in its own setup | A Shop test assumes `configuration/sales/checkout.spec.ts` enabled it |
| A product test creates the attribute family it needs | A product test relies on the family spec running first |
| Reading the chain to decide what setup is required | Encoding the chain as file order, numeric prefixes, or `describe.serial` |

Use the dependency chain for understanding, scenario planning and discoverability.
Never for correctness.

Concretely, this means:

- **No numeric filename prefixes** (`01-attributes.spec.ts`) to force an order.
- **No `test.describe.serial`** to make a file's tests lean on each other. There
  are none left in any suite, and none should return. The domain almost never
  requires it — an accumulating price history can be built inside one test.
- **No setup-only tests.** A `test()` whose job is to create data for the tests
  below it is a `beforeEach` wearing a costume: it makes the file order-dependent
  and reports a green "test" that guarantees nothing.
- **No cross-suite assumptions.** The Admin and Shop projects are launched by
  separate commands and can run in either order, or alone.

### Pass data explicitly, never through disk or module state

The Shop suite used to hand the "current product" between tests through a
`product-data.json` file on disk, read back by every checkout page object. That
mechanism has been **removed**, and with it the setup-only `should create …
product` tests that existed to populate it. Do not reintroduce it in any form —
a JSON file, a module-level `let`, or a `beforeAll` that stashes the name.

The shape now in use: the spec creates what it needs in `beforeEach`, holds the
name in a local, and passes it in.

```ts
test.beforeEach(async ({ adminPage }) => {
    productName = `Simple-${uniqueStamp()}`;

    await new ProductCreatePage(adminPage).createProduct({ name: productName, … });
});

test("should …", async ({ shopPage }) => {
    await new SimpleProductCheckout(shopPage).checkout(productName);
});
```

Why it matters beyond tidiness: a disk handoff survives the run, so a spec
executed alone will happily buy a product left by a run from last week; there can
only ever be one "current product", so no two tests in a file can own different
data; and the dependency is invisible in the spec body, so nothing tells a reader
the test needs another test to have run.

## Establishing an admin prerequisite from a Shop test

Take guest checkout, the case the suite currently gets wrong — and a good example
of why the prerequisites have to come from reading the code rather than the
screen. A guest reaches the checkout page only if **both** hold:

| Prerequisite | Enforced in |
|---|---|
| `sales.checkout.shopping_cart.allow_guest_checkout` is on | `OnepageController::index` redirects to sign-in otherwise |
| Every cart item's product has `guest_checkout` set | `Checkout/src/Models/Cart.php` — `$item->product->getAttribute('guest_checkout')` |

Nothing in `tests/checkout/simple-checkout.spec.ts` establishes either. Its guest
test passes only while an earlier run happened to leave the setting on and the
product it inherited happened to allow it.

The shape that owns its prerequisites, using the Shop suite's own admin page
objects:

```ts
test.describe("guest checkout", () => {
    let checkoutConfig: CheckoutConfigurationPage;
    let guestCheckoutWasEnabled: boolean;
    let productName: string;

    test.beforeEach(async ({ adminPage }) => {
        checkoutConfig = new CheckoutConfigurationPage(adminPage);
        guestCheckoutWasEnabled = await checkoutConfig.isGuestCheckoutEnabled();

        await checkoutConfig.setGuestCheckout(true);

        productName = `Simple-${uniqueStamp()}`;

        await new ProductCreatePage(adminPage).createProduct({
            type: "simple",
            sku: `SKU-${uniqueStamp()}`,
            name: productName,
            price: 199,
            weight: 1,
            inventory: 100,
            guestCheckout: true,
        });
    });

    test.afterEach(async () => {
        await checkoutConfig.setGuestCheckout(guestCheckoutWasEnabled);
    });

    test("should let a guest place an order without signing in", async ({ shopPage }) => {
        const checkout = new SimpleProductCheckout(shopPage);

        await checkout.guestCheckout(productName);

        await checkout.expectOrderPlaced();
    });
});
```

Five things make this correct:

1. The Shop test **reads** the original setting before changing it.
2. It **sets** the value it needs rather than toggling.
3. It **creates its own product**, with the product-level prerequisite the code
   requires, and passes the name in — instead of relying on a product some
   earlier test happened to leave behind.
4. It **restores** the original setting in `afterEach`, so the next spec is
   unaffected.
5. It asserts the **customer-visible** outcome, not the admin save toast — the
   admin side of that is the Admin suite's job.

The named methods are illustrative. `CheckoutConfigurationPage` today exposes the
group-level `readSettings()` / `applySettings(...)` pair rather than a
per-setting getter and setter — check the page object before writing against it,
and extend it in whichever shape it already uses. The principle is in
[Set, never toggle](#set-never-toggle).

The matching negative test is worth more than the positive one, and costs almost
nothing on top: set the config off, and assert the guest is sent to sign-in
rather than reaching payment. That is the assertion that proves the setting is
wired to anything.

If the prerequisite is data rather than configuration, the same rule applies: the
Shop test creates the product, the category or the customer it needs, through
`Shop/tests/e2e-pw/pages/admin/…`, and cleans it up.

## Set, never toggle

A configuration control in Bagisto is a `label[for=…]` over a hidden checkbox, so
a click **flips** it. A test that clicks to "enable" something enables it only if
it was off — and on the second run of the same suite against the same database,
it disables it instead. The behaviour of every later spec then depends on how
many times that file has run.

`OmnibusAdminPage` already models this correctly and is the pattern to copy:

```ts
async enableOmnibus() {
    await this.visitConfig();

    if (!(await this.enableCheckbox.isChecked())) {
        await this.enableToggle.click();
    }
}

async isOmnibusEnabled(): Promise<boolean> {
    return this.enableCheckbox.isChecked();
}
```

The read-back method is not decoration — it is what lets a caller capture the
original value for restoration. Give every configuration page object both: a
setter that is idempotent, and a reader.

`CheckoutConfigurationPage` now models this at the level of a whole settings
group — `readSettings()` returns the current values and `applySettings(...)`
writes a given set — which is what lets its spec capture the originals once and
restore them wholesale. Either shape is fine; what is not fine is a method that
clicks a label unconditionally, because a "should enable X" test written on top
of it disables X on every other run against the same database.

## The global configuration surface

Anything under `admin/configuration/**` is global: one value, shared by every
later spec and by the storefront. Treat a change to any of it as borrowed state
that must be given back.

The areas that most often bite, because a Shop spec silently depends on them:

| Area | Why it matters downstream |
|---|---|
| Checkout — guest checkout, cart page, mini cart | Whole storefront checkout flows change shape |
| Catalog — products, inventory, omnibus, rich snippets | Product page content, stock messaging, price display |
| Customer — settings, address, captcha | Registration and account flows, and whether captcha blocks a form |
| Sales — payment methods, shipping methods, taxes | Which options appear at checkout, and every total |
| Email and notifications | Whether a flow completes or waits on mail |
| Channels, currencies, locales, exchange rates, inventory sources | Prices, formatting, availability across the whole storefront |
| Appearance — themes, published sections | What renders on the storefront home page |

The configuration specs now **read the originals and put them back** — see
`tests/configuration/sales/checkout.spec.ts` with
`CheckoutConfigurationPage.readSettings()` / `applySettings()`. That is the
convention; a new spec that changes a global setting and leaves is a regression
against it.

## A worked example

`Admin/tests/e2e-pw/tests/catalog/product/omnibus/omnibus-shop.spec.ts` is the
reference for an Admin→Shop test, and it is worth reading before writing one.
It used to be the cautionary tale in this file; the defects below were fixed
during the suite cleanup, and the list is kept because each one is a shape that
tends to come back.

What it does:

- **Enables omnibus itself** rather than assuming `omnibus-admin.spec.ts` ran.
- Verifies on `shopPage` what a customer would actually see.
- Models a genuine state chain: base price → special price → lower → higher.
- Gives each test its own product, drives the edit through `ProductEditPage`,
  addresses the row by `productName`, and restores the setting in `afterEach`.

The shapes it no longer has, and which should not return:

| Shape | Consequence |
|---|---|
| `test.describe.serial` with shared `beforeAll` state | A later test cannot run alone; a failure in the first cascades |
| Changing a global setting and never restoring it | Every later spec, and the next run, sees the changed value |
| A spec-local helper holding raw selectors | The spec owns locators; a UI change breaks it silently |
| `.nth(1)` on a row icon to open the product | Opens whatever is second in the grid, not the product it created — while `productName` is in scope |
| `waitForLoadState("networkidle")` between steps | Not tied to the state it actually needs — see [locators.md](locators.md) for the one sanctioned use |

## Organising each suite

**Admin — mirror the admin menu.** `tests/catalog/`, `tests/customers/`,
`tests/marketing/`, `tests/settings/`, `tests/configuration/`, `tests/appearance/`.
A person who can find the screen can find its spec. The standing exception is
ACL: every ACL spec lives in `tests/settings/acl/`, including the ones covering
other sections.

**Shop — mirror the customer journey.** The suite already groups this way at the
top level: `auth`, `cart`, `checkout/`, `customer`, `compare`, `filter`, `home`,
`review`, `rma`, `search`, `wishlist`. New storefront coverage joins the journey
it belongs to; `checkout/` is subdivided by product type because checkout genuinely
differs per type.

The one place to be careful is `Shop/tests/promotion/`. It is organised by the
admin rule-condition attribute — `cart-rules/product-attributes/sku.spec.ts`,
`…/color.spec.ts`, `…/width.spec.ts` and so on — over fifty files whose bodies
differ only in the attribute string passed to `addCondition` and whose assertion
is identical. That is a shape to stop extending: if a new condition attribute
proves nothing the existing ones do not, add a case to a parameterised spec
rather than a fortieth file. See [test-design.md](test-design.md).

Neither suite uses ordering-carrying filenames, and neither should start.
