## Running Tests

### Run All Tests

```bash
php artisan test --compact
```

### Run Specific Test Suite

```bash
php artisan test --testsuite="Shop Feature Test"
php artisan test --testsuite="Admin Feature Test"
php artisan test --testsuite="Core Unit Test"
```

### Run Specific Test File

```bash
php artisan test --compact packages/Webkul/Shop/tests/Feature/Checkout/CheckoutTest.php
```

### Run Test with Filter

```bash
php artisan test --compact --filter=testName
```

### Run Tests for Specific Package

```bash
# Shop tests
php artisan test --compact packages/Webkul/Shop/tests/

# Admin tests
php artisan test --compact packages/Webkul/Admin/tests/

# Core tests
php artisan test --compact packages/Webkul/Core/tests/
```

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

### Create Feature Test

```bash
php artisan make:test --pest packages/Webkul/Shop/tests/Feature/Checkout/MyNewTest
```

### Create Unit Test

```bash
php artisan make:test --pest --unit packages/Webkul/Core/tests/Unit/MyNewTest
```

## Basic Test Structure

```php
<?php

namespace Webkul\Shop\Tests\Feature\Checkout;

use Webkul\Shop\Tests\ShopTestCase;

it('should pass basic test', function () {
    expect(true)->toBeTrue();
});

it('should return successful response', function () {
    $response = $this->getJson('/api/categories');

    $response->assertStatus(200);
});
```

## Assertions

Use specific assertions (`assertSuccessful()`, `assertNotFound()`) instead of `assertStatus()`:

| Use | Instead of |
|-----|------------|
| `assertSuccessful()` | `assertStatus(200)` |
| `assertNotFound()` | `assertStatus(404)` |
| `assertForbidden()` | `assertStatus(403)` |

## Mocking

Import mock function before use:

```php
use function Pest\Laravel\mock;
```

## Datasets

Use datasets for repetitive tests:

```php
it('has valid emails', function (string $email) {
    expect($email)->not->toBeEmpty();
})->with([
    'james' => 'james@bagisto.com',
    'john'  => 'john@bagisto.com',
]);
```

## Architecture Testing

Pest includes architecture testing to enforce code conventions — available on
both lines (**2.4** runs Pest 3, **2.5** Pest 5):

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
