## Two lines, one skill

This skill is shared by every local workspace. The conventions below apply to both lines unless a
section says otherwise; the differences are always called out as **2.4** (Pest 3) versus
**master / 2.5 and later** (Pest 5). Never use master-only infrastructure (shared datasets, the
Product and Sales benches, `setConfig()`, `toBePrice()`) in the 2.4 workspace — it does not exist
there, and the 2.4 conventions in [suite-layout.md](suite-layout.md) are the ones to follow.

## Running Tests

### Run All Tests

```bash
vendor/bin/pest --compact
```

### Run Specific Test Suite

```bash
vendor/bin/pest --testsuite="Shop Feature Test"
vendor/bin/pest --testsuite="Admin Feature Test"
vendor/bin/pest --testsuite="Core Unit Test"
```

### Run Specific Test File

```bash
vendor/bin/pest --compact packages/Webkul/Shop/tests/Feature/Checkout/CheckoutTest.php
```

### Run Test with Filter

```bash
vendor/bin/pest --compact --filter="should place an order"
```

### Run Tests for Specific Package

```bash
vendor/bin/pest --compact packages/Webkul/Shop/tests/
vendor/bin/pest --compact packages/Webkul/Admin/tests/
vendor/bin/pest --compact packages/Webkul/Core/tests/
```

`php artisan test` accepts the same arguments.

### Run in parallel, and the stale-database trap

```bash
vendor/bin/pest --parallel
```

Parallel runs create one database per process — `{DB_DATABASE}_test_1`,
`_test_2`, … — as many as the machine has CPU cores, on MySQL, MariaDB and
PostgreSQL alike. With `DB_DATABASE=bagisto` on an 8-core machine that is
`bagisto_test_1` through `bagisto_test_8`.

**Those databases are not migrated again on the next run.** After a schema
change they hold the old schema, and the failures that follow look like broken
code rather than a stale fixture. Drop them, reinstall, then re-run:

```bash
php artisan tinker --execute="for (\$i = 1; \$i <= 8; \$i++) { try { DB::statement(\"DROP DATABASE IF EXISTS bagisto_test_{\$i}\"); } catch (\Exception \$e) {} }"

php artisan bagisto:install --no-interaction

vendor/bin/pest --parallel --no-coverage
```

Match the loop bound to the core count, or it leaves databases behind.

## Creating New Tests

```bash
php artisan make:test --pest packages/Webkul/Shop/tests/Feature/Checkout/MyNewTest
php artisan make:test --pest --unit packages/Webkul/Core/tests/Unit/MyNewTest
```

## File Layout

Every Pest file follows the same order, top to bottom. Nothing goes below the tests.

```php
<?php

use Webkul\Category\Models\Category;
use Webkul\Category\Models\CategoryTranslation;

use function Pest\Laravel\getJson;

dataset('currency positions', [
    'left' => [CurrencyPositionEnum::LEFT, '%1$s%2$s'],
    'right' => [CurrencyPositionEnum::RIGHT, '%2$s%1$s'],
]);

/**
 * Create a category with a translation in the current locale.
 */
function createTestCategory(): Category
{
    return Category::factory()->has(CategoryTranslation::factory(), 'translations')->create();
}

beforeEach(function () {
    $this->setConfig('catalog.products.storefront.products_per_page', 12);
});

// ============================================================================
// Listing
// ============================================================================

it('should list the products of a category', function () {
    // ...
});
```

1. **Imports** — `use` statements, then `use function Pest\Laravel\...` for the request helpers.
2. **`dataset()` declarations** local to the file.
3. **Global helper functions**, each with a docblock, before anything that calls them.
4. **Hooks** — `beforeEach()` / `afterEach()`.
5. **Tests**, grouped under `// ====` banners with a Title Case heading. A banner never sits above
   the helpers, and a banner is never left with nothing under it.

Rules for helpers:

- A helper is a global function, so its name must be unique across the **whole** suite — Pest
  loads every file. Grep `packages/*/*/tests` before choosing a name; a clash is a fatal error.
- Inside a helper use `test()->createSimpleProduct()`, `test()->setConfig(...)` and so on rather
  than passing `$this` in as a parameter.
- Keep helpers to fixture building and small payloads. Behaviour shared by many files belongs in
  the package's `tests/Concerns` trait instead (see below).
- Docblocks are one line, two at most: a capitalised sentence with a full stop. There are **no
  comments inside test or helper bodies** — no `// Arrange`, `// Act`, `// Assert`, no narration.
  If a step needs prose, extract a named helper.
- Multi-clause conditions go multiline with the boolean operator leading each line, exactly as in
  production code.

## Naming

Tests read as behaviour: `it('should refuse a refund of more than the quantity left to refund', ...)`.
Say what the system does, not what the test does. Avoid `test('...')` and names that repeat the
route or method under test.

## Assertions

Use the semantic response assertions — `assertStatus(n)` is only acceptable where no helper exists
(a `304`, for example):

| Use | Instead of |
|-----|------------|
| `assertOk()` | `assertStatus(200)` |
| `assertRedirect()` / `assertRedirectToRoute()` | `assertStatus(302)` |
| `assertBadRequest()` | `assertStatus(400)` |
| `assertUnauthorized()` | `assertStatus(401)` |
| `assertForbidden()` | `assertStatus(403)` |
| `assertNotFound()` | `assertStatus(404)` |
| `assertUnprocessable()` | `assertStatus(422)` |
| `assertServerError()` | `assertStatus(500)` |

An admin who lacks a permission is answered with **401** by the Bouncer, so ACL tests use
`assertUnauthorized()`; the granted case asserts the real outcome (`assertOk()`, a redirect, …),
never "not 401".

Assert the outcome, not the status alone: the row in the database (`assertDatabaseHas`,
`assertDatabaseMissing`), the model state after `refresh()`, the mail or event through
`Mail::fake()` / `Event::fake()` / `Notification::fake()`, the session flash, the JSON path.
Money is compared with the currency's precision — on master use `expect($value)->toBePrice(100)`
or `$this->assertPrice(100, $value)`; on 2.4 use `$this->assertPrice()` from `CoreAssertions`.

Booleans in `assertDatabaseHas` are passed as `true` / `false`, never `1` / `0`: a boolean column
compared with an integer fails on PostgreSQL.

## The database is populated

Tests run inside `DatabaseTransactions` against the developer's own database, which already holds
products, orders, customers and categories. Therefore:

- Never assert absolute counts or `records.0` / `data.0` positions on an unfiltered listing. Filter
  the request to the rows the test created, sort by `created_at-desc`, or assert relative to a
  reading taken before the fixture was created.
- Never rely on seeded ids beyond customer groups 1 (guest), 2 (general), 3 (wholesale), the default
  channel, locale, currency and attribute family. Resolve attributes by code
  (`getAttributeMap()['price']`), options through their attribute, and currencies or locales by a
  code the test generates and checks for uniqueness.
- Never delete or rename seeded rows to reach a branch; create what the branch needs instead.
- Configuration written by a test must be scoped to the current channel and locale, because the
  populated database carries channel-scoped rows that shadow global ones (master: `setConfig()`
  does this for you).

## Fixtures and helpers

### master / 2.5 and later

| Helper | Lives in | What it gives you |
|---|---|---|
| `ProductTestBench` | `packages/Webkul/Product/tests/Concerns` | `createSimpleProduct(['price' => ['float_value' => 100]])`, `createVirtualProduct`, `createDownloadableProduct`, `createConfigurableProduct([prices])`, `createGroupedProduct`, `createBundleProduct`, `createProductOfType($type)`, `setProductStock($product, $qty)`, the `storeAndUpdate…` route helpers, `getAttributeMap()` |
| `OrderTestBench` | `packages/Webkul/Sales/tests/Concerns` | `createOrder($attributes, $items, $customer)`, `createGuestOrder`, `createOrderItem`, `invoiceOrder`, `shipOrder` — fully addressed orders with derived totals |
| `ConfiguresSettings` | `packages/Webkul/Core/tests/Concerns` (on every TestCase) | `setConfig('sales.taxes.calculation.based_on', 'shipping_address')` or `setConfig([...])` |
| `CreatesUploads` | `packages/Webkul/Core/tests/Concerns` (on every TestCase) | `uploadedFileWithContents('shell.php', $contents)` — a real upload whose type is detected from its contents, for tests where `UploadedFile::fake()` would trust the file name or cannot be stored on a cart item |
| `CoreAssertions` | `packages/Webkul/Core/tests/Concerns` | `assertPrice()`, `assertModelWise()` |
| `AdminTestBench` | `packages/Webkul/Admin/tests/Concerns` | `loginAsAdmin()`, `loginAsAdminWithPermissions([...])` |
| Shop concerns | `packages/Webkul/Shop/tests/Concerns` | `loginAsCustomer`, `actAsCustomerGroup`, `addProductToCart` / `addProductByType`, `prepareCartForCheckout`, `placeOrder`, `assertOrderPlaced`, `assertCartDiscount`, `createCartRuleForPricing`, `createCatalogRuleForPricing`, `setCustomerGroupPrice`, `setSpecialPriceOnProduct`, `listedPrice` |
| `ProvidePaymentHelpers` | `packages/Webkul/Payment/tests/Concerns` | `createCartWithItems($paymentMethod)` for the gateway packages |

The Admin TestCase resolves the theme registry per request, so an admin test may render a
storefront page or mail without breaking the admin assets of the next request.

### 2.4

The 2.4 suite has `AdminTestBench`, `ShopTestBench`, `CoreAssertions`, `FPCTestBench` and
`ProvidePaymentHelpers` only. Products come from `Webkul\Faker\Helpers\Product` (`ProductFaker`)
and orders from `Order::factory()->has(...)` chains; configuration is written with
`CoreConfig::updateOrCreate` in the test. Do not port the master benches back into 2.4 tests.

## Datasets

File-local datasets go at the top of the file (see *File Layout*):

```php
it('has valid emails', function (string $email) {
    expect($email)->not->toBeEmpty();
})->with([
    'james' => 'james@bagisto.com',
    'john' => 'john@bagisto.com',
]);
```

**master / 2.5 and later** also has shared datasets in `tests/Datasets/`, registered with
`sharedDataset()` (defined in `tests/Pest.php`) so that files under `packages/` can use them —
a plain `dataset()` declared there is scoped to `tests/` and invisible to package tests:

| Dataset | Arguments | Use it for |
|---|---|---|
| `customer groups` | `array $ruleGroups, ?int $customerGroupId` | a promotion or price limited to groups, shopped by a member of that group (`null` is a guest) |
| `product types` | `string $type` | every sellable type, with `createProductOfType()` / `addProductByType()` |
| `stockable product types` / `non-stockable product types` | `string $type` | flows that do or do not need shipping |
| `shoppers` | `bool $signedIn` | guest versus signed-in behaviour |
| `special price windows` | `?int $fromInDays, ?int $toInDays, float $expectedPrice` | whether a special price is in force |

```php
it('should apply a fixed cart rule discount to a simple product', function (array $ruleGroups, ?int $customerGroupId) {
    $product = $this->createSimpleProduct(['price' => ['float_value' => 500]]);

    $this->createCartRuleForPricing(['action_type' => 'by_fixed', 'discount_amount' => 50], $ruleGroups);

    $this->actAsCustomerGroup($customerGroupId);

    $this->assertCartDiscount($this->addProductToCart($product->id)->assertOk(), 50);
})->with('customer groups');
```

Prefer a dataset over copies of a test that differ only in the customer group, product type or
date window. **2.4** has no `tests/Datasets` directory and no `sharedDataset()`; keep datasets
file-local there.

## Mocking

Import mock function before use:

```php
use function Pest\Laravel\mock;
```

Mock only what the test cannot own (an HTTP gateway, the clock); never mock the repository the
behaviour under test lives in.

## Architecture Testing

Pest includes architecture testing to enforce code conventions — available on
both lines (**2.4** runs Pest 3, **master** Pest 5):

```php
arch('controllers')
    ->expect('Webkul\Admin\Http\Controllers')
    ->toExtendNothing()
    ->toHaveSuffix('Controller');

arch('models')
    ->expect('Webkul\Core\Models')
    ->toExtend('Illuminate\Database\Eloquent\Model');

arch('no debugging')
    ->expect(['dd', 'dump', 'ray'])
    ->not->toBeUsed();
```
