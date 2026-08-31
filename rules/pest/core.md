## Pest

- This project uses Pest for testing. Create tests: `php artisan make:test --pest {name}`.
- Run tests: `php artisan test --compact` or filter: `php artisan test --compact --filter=testName`.
- Do NOT delete tests without approval.
- CRITICAL: ALWAYS use `search-docs` tool for version-specific Pest documentation and updated code examples.
- IMPORTANT: Activate `bagisto-pest-testing` every time you're working with a Pest or testing-related task.
- IMPORTANT: Activate `bagisto-playwright-testing` for anything under `tests/e2e-pw/`, and `bagisto-change-verification` before calling any change done.
