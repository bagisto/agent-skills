## Adding Tests to a New Package

If you add tests to a new package, you need to:

1. **Register in Pest.php:** Add the test case binding:

```php
uses(Webkul\NewPackage\Tests\NewPackageTestCase::class)->in('../packages/Webkul/NewPackage/tests');
```

2. **Register in composer.json (autoload-dev):**

```json
"autoload-dev": {
    "psr-4": {
        "Webkul\\NewPackage\\Tests\\": "packages/Webkul/NewPackage/tests"
    }
}
```

3. **Register in phpunit.xml:** Add a new testsuite:

```xml
<testsuite name="New Package Test">
    <directory suffix="Test.php">packages/Webkul/NewPackage/tests</directory>
</testsuite>
```

4. **Run composer dump-autoload:**

```bash
composer dump-autoload
```

## Common Pitfalls

- Not importing `use function Pest\Laravel\mock;` before using mock
- Using `assertStatus(200)` instead of `assertSuccessful()`
- Forgetting to run `composer dump-autoload` after adding test namespace
- Not registering test case in `tests/Pest.php`
- Not adding testsuite to `phpunit.xml` for package-specific testing
- Deleting tests without approval
- Forgetting to register test namespace in composer.json autoload-dev

## Testing Best Practices

- Test happy paths, failure paths, and edge cases.
- Use factories for model creation in tests.
- Follow existing test patterns in the package.
- Use `$this->faker` or `fake()` for generating test data.
- Keep tests focused and independent.
