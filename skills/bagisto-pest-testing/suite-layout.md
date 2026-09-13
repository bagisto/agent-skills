## Bagisto Testing Structure

This file describes both lines. Sections marked **master / 2.5 and later** do not apply to the
2.4 workspace, and the **2.4** sections must stay as they are so that work on 2.4 keeps following
its own conventions.

### Test Locations

Tests live inside the package they exercise, under `packages/Webkul/{Package}/tests/`. Every
package with tests has a `{Package}TestCase` and, where it shares fixtures, a `Concerns/` trait:

```
packages/Webkul/
├── Admin/tests/
│   ├── AdminTestCase.php              # base case; master resolves the theme registry per request
│   ├── Concerns/AdminTestBench.php    # loginAsAdmin(), loginAsAdminWithPermissions()
│   ├── Fixtures/                      # theme section classes used by the appearance tests
│   └── Feature/...
├── Shop/tests/
│   ├── ShopTestCase.php
│   ├── Concerns/                      # ShopTestBench (2.4: one trait; master: Auth/Cart/Checkout/Pricing/Assertion helpers)
│   └── Feature/...
├── Core/tests/
│   ├── CoreTestCase.php
│   ├── Concerns/CoreAssertions.php    # master also has ConfiguresSettings (setConfig)
│   └── Unit/...
├── Product/tests/                     # master only: ProductTestCase, Concerns/ProductTestBench, Unit/
├── Sales/tests/                       # master only: SalesTestCase, Concerns/OrderTestBench, Unit/
└── ...
tests/
├── Pest.php                           # TestCase bindings, custom expectations, sharedDataset() (master)
├── TestCase.php                       # DatabaseTransactions (+ ConfiguresSettings on master)
└── Datasets/                          # master only: shared datasets
```

### Available Test Suites — master / 2.5 and later

| Test Suite | Location |
|---|---|
| Unit Test | `tests/Unit` |
| Admin Feature Test | `packages/Webkul/Admin/tests/Feature` |
| Category Unit Test | `packages/Webkul/Category/tests/Unit` |
| Core Unit Test | `packages/Webkul/Core/tests/Unit` |
| Customer Unit Test | `packages/Webkul/Customer/tests/Unit` |
| DataGrid Unit Test | `packages/Webkul/DataGrid/tests/Unit` |
| EUWithdrawal Feature Test | `packages/Webkul/EUWithdrawal/tests/Feature` |
| FPC Unit Test / FPC Feature Test | `packages/Webkul/FPC/tests/Unit` / `Feature` |
| Installer Feature Test | `packages/Webkul/Installer/tests/Feature` |
| Omnibus Feature Test | `packages/Webkul/Omnibus/tests/Feature` |
| PayGlocal Unit Test / PayGlocal Feature Test | `packages/Webkul/PayGlocal/tests/Unit` / `Feature` |
| PayU Unit Test / PayU Feature Test | `packages/Webkul/PayU/tests/Unit` / `Feature` |
| Product Unit Test | `packages/Webkul/Product/tests/Unit` |
| Razorpay Unit Test / Razorpay Feature Test | `packages/Webkul/Razorpay/tests/Unit` / `Feature` |
| Rule Unit Test | `packages/Webkul/Rule/tests/Unit` |
| Sales Unit Test | `packages/Webkul/Sales/tests/Unit` |
| Shipping Unit Test | `packages/Webkul/Shipping/tests/Unit` |
| Shop Feature Test | `packages/Webkul/Shop/tests/Feature` |
| Stripe Unit Test / Stripe Feature Test | `packages/Webkul/Stripe/tests/Unit` / `Feature` |
| Tax Unit Test | `packages/Webkul/Tax/tests/Unit` |

Run one with `vendor/bin/pest --testsuite="Sales Unit Test"`. Packages without a `tests/`
directory (PhonePe, Checkout, RMA, …) have no suite; a `<testsuite>` pointing at a missing path
makes PHPUnit error, so write the tests first (see [new-package.md](new-package.md)).

### Available Test Suites — 2.4

| Test Suite | Location |
|---|---|
| Admin Feature Test | `packages/Webkul/Admin/tests/Feature` |
| Core Unit Test | `packages/Webkul/Core/tests/Unit` |
| Customer Unit Test | `packages/Webkul/Customer/tests/Unit` |
| DataGrid Unit Test | `packages/Webkul/DataGrid/tests/Unit` |
| EUWithdrawal Feature Test | `packages/Webkul/EUWithdrawal/tests/Feature` |
| FPC Unit Test / FPC Feature Test | `packages/Webkul/FPC/tests/Unit` / `Feature` |
| Installer Feature Test | `packages/Webkul/Installer/tests/Feature` |
| PayGlocal Unit Test / PayGlocal Feature Test | `packages/Webkul/PayGlocal/tests/Unit` / `Feature` |
| PayU Unit Test / PayU Feature Test | `packages/Webkul/PayU/tests/Unit` / `Feature` |
| Razorpay Unit Test / Razorpay Feature Test | `packages/Webkul/Razorpay/tests/Unit` / `Feature` |
| Shop Feature Test | `packages/Webkul/Shop/tests/Feature` |
| Stripe Unit Test / Stripe Feature Test | `packages/Webkul/Stripe/tests/Unit` / `Feature` |

2.4 has no Product, Sales, Rule, Tax, Shipping or Category suite and no `tests/Unit`.

## Pest.php Configuration

`tests/Pest.php` binds one TestCase per package directory, in alphabetical order. On master it also
defines the `toBePrice()` expectation and the `sharedDataset()` helper:

```php
<?php

use Pest\Repositories\DatasetsRepository;
use Webkul\Admin\Tests\AdminTestCase;
use Webkul\Category\Tests\CategoryTestCase;
use Webkul\Core\Tests\CoreTestCase;
// ... one import per package with tests

uses(AdminTestCase::class)->in('../packages/Webkul/Admin/tests');
uses(CategoryTestCase::class)->in('../packages/Webkul/Category/tests');
uses(CoreTestCase::class)->in('../packages/Webkul/Core/tests');
// ... Customer, DataGrid, EUWithdrawal, FPC, Installer, Omnibus, PayGlocal, Payment, PayU,
//     Product, Razorpay, Rule, Sales, Shipping, Shop, Stripe, Tax

expect()->extend('toBePrice', function (float $expected, ?int $decimal = null) {
    $decimal ??= core()->getCurrentCurrency()->decimal;

    expect(number_format((float) $this->value, $decimal))->toBe(number_format($expected, $decimal));

    return $this;
});

/**
 * Register a dataset every package's tests can use, not only the ones under tests/.
 */
function sharedDataset(string $name, Closure|iterable $dataset): void
{
    DatasetsRepository::set($name, $dataset, dirname(__DIR__));
}
```

The **2.4** `tests/Pest.php` binds Admin, Core, Customer, DataGrid, EUWithdrawal, FPC, Installer,
PayGlocal, Payment, PayU, Razorpay, Shop and Stripe and still carries the Pest starter
`toBeOne` expectation; leave it as it is.

### Test Case Structure

Each package has its own test case that extends `Tests\TestCase` (which applies
`DatabaseTransactions`) and mixes in the concerns its tests need:

```php
// packages/Webkul/Shop/tests/ShopTestCase.php
<?php

namespace Webkul\Shop\Tests;

use Tests\TestCase;
use Webkul\Core\Tests\Concerns\CoreAssertions;
use Webkul\Shop\Tests\Concerns\ShopTestBench;

class ShopTestCase extends TestCase
{
    use CoreAssertions, ShopTestBench;
}
```

Concerns are plain traits: every method carries a docblock, members are grouped by visibility
(public before protected) and related helpers sit together (all the `create…Product` factories,
then the route-based helpers, then the internal ones).

## Composer.json Autoload Configuration

Package namespaces are registered in root `composer.json` under `autoload`; test namespaces under
`autoload-dev`, sorted alphabetically:

```json
"autoload-dev": {
    "psr-4": {
        "Tests\\": "tests/",
        "Webkul\\Admin\\Tests\\": "packages/Webkul/Admin/tests",
        "Webkul\\Category\\Tests\\": "packages/Webkul/Category/tests",
        "Webkul\\Core\\Tests\\": "packages/Webkul/Core/tests",
        ...
    }
}
```

On **2.4** the list stops at the packages named in its suite table above.
