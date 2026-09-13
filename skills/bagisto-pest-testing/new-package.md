## Adding Tests to a New Package

The steps are the same on both lines; only the lists you add to differ (see
[suite-layout.md](suite-layout.md) for what each line already has).

1. **Create the test case** at `packages/Webkul/NewPackage/tests/NewPackageTestCase.php`,
   extending `Tests\TestCase` and mixing in the concerns the tests need:

```php
<?php

namespace Webkul\NewPackage\Tests;

use Tests\TestCase;
use Webkul\Core\Tests\Concerns\CoreAssertions;

class NewPackageTestCase extends TestCase
{
    use CoreAssertions;
}
```

   On master add `Webkul\Product\Tests\Concerns\ProductTestBench` and
   `Webkul\Sales\Tests\Concerns\OrderTestBench` when the tests need products or orders rather
   than writing new factories.

2. **Register in Pest.php**, keeping the imports and bindings alphabetical:

```php
uses(NewPackageTestCase::class)->in('../packages/Webkul/NewPackage/tests');
```

3. **Register in composer.json (autoload-dev)**, alphabetically:

```json
"autoload-dev": {
    "psr-4": {
        "Webkul\\NewPackage\\Tests\\": "packages/Webkul/NewPackage/tests"
    }
}
```

4. **Register in phpunit.xml** with the package comment and the naming the other suites use —
   `NewPackage Unit Test` for `tests/Unit`, `NewPackage Feature Test` for `tests/Feature`:

```xml
<!-- NewPackage package testsuites. -->
<testsuite name="NewPackage Unit Test">
    <directory suffix="Test.php">packages/Webkul/NewPackage/tests/Unit</directory>
</testsuite>
```

   Point it at a directory that exists; a missing path makes PHPUnit error.

5. **Run composer dump-autoload**:

```bash
composer dump-autoload
```

6. **Update the suite lists** — the `Testing` section of `CLAUDE.md` in the workspace and the
   matching table in [suite-layout.md](suite-layout.md) for the line you are on.

## Common Pitfalls

- A global helper name that already exists in another test file: Pest loads every file, so the
  duplicate is a fatal error. Grep the suite first.
- Declaring a shared dataset with `dataset()` in `tests/Datasets` on master: it is scoped to
  `tests/` and package tests get `DatasetDoesNotExist`. Use `sharedDataset()`.
- Asserting `'status' => 1` in `assertDatabaseHas` for a boolean column: fails on PostgreSQL. Use
  `true` / `false`.
- Assuming the database is empty or that seeded ids are stable (see *The database is populated*
  in [writing-tests.md](writing-tests.md)).
- Using `assertStatus(200)` instead of `assertOk()`, or "not 401" instead of the granted outcome.
- Comments inside test bodies, helpers without a docblock, helpers declared below the tests.
- Forgetting to run `composer dump-autoload` after adding a test namespace.
- Not registering the test case in `tests/Pest.php` or the suite in `phpunit.xml`.
- Deleting tests without approval.

## Testing Best Practices

- Test the happy path, every refusal branch the controller has, and the boundary (last unit of
  stock, quantity left to invoice, the default channel, the last admin).
- Prefer the package benches over hand-rolled factory chains; add a bench method when three tests
  need the same fixture.
- Follow the file layout in [writing-tests.md](writing-tests.md): imports, datasets, helpers,
  hooks, banners, tests.
- Use `fake()` for data, but generate codes that must be unique (currency, locale, SKU) and check
  them against the database when the column is unique.
- Keep tests focused and independent; a test never depends on another test's rows.
