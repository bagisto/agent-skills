## Bagisto Testing Structure

### Test Locations

Bagisto tests are organized within packages in `packages/Webkul/{Package}/tests/`:

```
packages/Webkul/
├── Admin/
│   └── tests/
│       ├── AdminTestCase.php          # Base test case
│       ├── Concerns/
│       │   └── AdminTestBench.php     # Test helpers
│       └── Feature/
│           ├── ExampleTest.php
│           └── ...
├── Shop/
│   └── tests/
│       ├── ShopTestCase.php
│       ├── Concerns/
│       │   └── ShopTestBench.php
│       └── Feature/
│           ├── Checkout/
│           │   └── CheckoutTest.php
│           └── ...
├── Core/
│   └── tests/
│       ├── CoreTestCase.php
│       ├── Concerns/
│       │   └── CoreAssertions.php
│       ├── Unit/
│       └── Feature/
├── DataGrid/
│   └── tests/
│       ├── DataGridTestCase.php
│       └── Unit/
└── Installer/
    └── tests/
        ├── InstallerTestCase.php
        └── Feature/
```

### Available Test Suites

Bagisto has the following test suites configured in `phpunit.xml`:

| Test Suite | Location | Command |
|------------|----------|---------|
| Admin Feature Test | `packages/Webkul/Admin/tests/Feature` | `php artisan test --testsuite="Admin Feature Test"` |
| Core Unit Test | `packages/Webkul/Core/tests/Unit` | `php artisan test --testsuite="Core Unit Test"` |
| Customer Unit Test | `packages/Webkul/Customer/tests/Unit` | `php artisan test --testsuite="Customer Unit Test"` |
| DataGrid Unit Test | `packages/Webkul/DataGrid/tests/Unit` | `php artisan test --testsuite="DataGrid Unit Test"` |
| EUWithdrawal Feature Test | `packages/Webkul/EUWithdrawal/tests/Feature` | `php artisan test --testsuite="EUWithdrawal Feature Test"` |
| Installer Feature Test | `packages/Webkul/Installer/tests/Feature` | `php artisan test --testsuite="Installer Feature Test"` |
| PayU Unit Test | `packages/Webkul/PayU/tests/Unit` | `php artisan test --testsuite="PayU Unit Test"` |
| PayU Feature Test | `packages/Webkul/PayU/tests/Feature` | `php artisan test --testsuite="PayU Feature Test"` |
| Razorpay Unit Test | `packages/Webkul/Razorpay/tests/Unit` | `php artisan test --testsuite="Razorpay Unit Test"` |
| Razorpay Feature Test | `packages/Webkul/Razorpay/tests/Feature` | `php artisan test --testsuite="Razorpay Feature Test"` |
| Shop Feature Test | `packages/Webkul/Shop/tests/Feature` | `php artisan test --testsuite="Shop Feature Test"` |
| Stripe Unit Test | `packages/Webkul/Stripe/tests/Unit` | `php artisan test --testsuite="Stripe Unit Test"` |
| Stripe Feature Test | `packages/Webkul/Stripe/tests/Feature` | `php artisan test --testsuite="Stripe Feature Test"` |

## Pest.php Configuration

Bagisto uses `tests/Pest.php` to register test cases for each package:

```php
<?php

uses(Webkul\Admin\Tests\AdminTestCase::class)->in('../packages/Webkul/Admin/tests');
uses(Webkul\Core\Tests\CoreTestCase::class)->in('../packages/Webkul/Core/tests');
uses(Webkul\Customer\Tests\CustomerTestCase::class)->in('../packages/Webkul/Customer/tests');
uses(Webkul\DataGrid\Tests\DataGridTestCase::class)->in('../packages/Webkul/DataGrid/tests');
uses(Webkul\EUWithdrawal\Tests\EUWithdrawalTestCase::class)->in('../packages/Webkul/EUWithdrawal/tests');
uses(Webkul\Installer\Tests\InstallerTestCase::class)->in('../packages/Webkul/Installer/tests');
uses(Webkul\Payment\Tests\PaymentTestCase::class)->in('../packages/Webkul/Payment/tests');
uses(Webkul\PayU\Tests\PayUTestCase::class)->in('../packages/Webkul/PayU/tests');
uses(Webkul\Razorpay\Tests\RazorpayTestCase::class)->in('../packages/Webkul/Razorpay/tests');
uses(Webkul\Shop\Tests\ShopTestCase::class)->in('../packages/Webkul/Shop/tests');
uses(Webkul\Stripe\Tests\StripeTestCase::class)->in('../packages/Webkul/Stripe/tests');
```

### Test Case Structure

Each package has its own test case that extends `Tests\TestCase`:

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

## Composer.json Autoload Configuration

### Production Autoload

Package namespaces are registered in root `composer.json`:

```json
"autoload": {
    "psr-4": {
        "Webkul\\Admin\\": "packages/Webkul/Admin/src",
        "Webkul\\Shop\\": "packages/Webkul/Shop/src",
        "Webkul\\Core\\": "packages/Webkul/Core/src",
        ...
    }
}
```

### Development Autoload

Test namespaces are registered in `autoload-dev`:

```json
"autoload-dev": {
    "psr-4": {
        "Tests\\": "tests/",
        "Webkul\\Admin\\Tests\\": "packages/Webkul/Admin/tests",
        "Webkul\\Core\\Tests\\": "packages/Webkul/Core/tests",
        "Webkul\\DataGrid\\Tests\\": "packages/Webkul/DataGrid/tests",
        "Webkul\\Installer\\Tests\\": "packages/Webkul/Installer/tests",
        "Webkul\\Shop\\Tests\\": "packages/Webkul/Shop/tests"
    }
}
```
