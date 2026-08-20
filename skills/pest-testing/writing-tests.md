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

Pest 3 includes architecture testing to enforce code conventions:

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
