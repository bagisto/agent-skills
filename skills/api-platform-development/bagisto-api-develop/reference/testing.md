# Testing + the cache cycle

## The golden rule

**After any REST change, run the affected resource's GraphQL test FIRST, then the REST test** — REST and GraphQL share the Processor/Provider, so a REST change can silently break GraphQL. Both green before the change is done.

## Pest feature tests

Tests live under `packages/Webkul/BagistoApi/tests/Feature/{GraphQL,RestApi,Admin/{GraphQL,RestApi,Audit,Web}}/`, one `<Resource>Test.php` per resource per transport.

```bash
# 1) GraphQL test for the changed resource (the regression check) — run FIRST
php artisan test packages/Webkul/BagistoApi/tests/Feature/GraphQL/<Resource>Test.php --parallel --processes=8

# 2) Then the REST test
php artisan test packages/Webkul/BagistoApi/tests/Feature/RestApi/<Resource>Test.php --parallel --processes=8

# Admin resources:
php artisan test packages/Webkul/BagistoApi/tests/Feature/Admin/GraphQL/<Resource>Test.php --parallel --processes=8
php artisan test packages/Webkul/BagistoApi/tests/Feature/Admin/RestApi/<Resource>Test.php --parallel --processes=8

# When shared logic (a base provider/processor) changed — the full GraphQL suite:
php artisan test --testsuite="BagistoApi GraphQL Test" --parallel --processes=8
```

- **Always run `--parallel`.** Match `--processes` to CPU cores; oversubscribing slows it down.
- **Disable xdebug** for a big speedup: `XDEBUG_MODE=off php artisan test …`.
- Paratest accepts **one path argument** — loop files sequentially, don't space-separate.
- Base classes: `BagistoApiTestCase` (key/auth/seed), `GraphQLTestCase`, `RestApiTestCase`, `AdminApiTestCase` (admin-token auth).
- Don't run unprompted full regression sweeps — run the targeted tests for what changed.

## Cache cycle (critical — tests clear caches)

Running `php artisan test` **clears the route + config cache**, which leaves responses slow and can hide a new endpoint. The cycle when adding/changing a resource:

```bash
# After editing a resource — pick up the new route (route cache now OFF, responses slow):
php artisan optimize:clear && php artisan bagisto-api-platform:clear-cache
#   …live-test the endpoint; the first GraphQL run may be stale — re-run if so…

# When done (and after any test session) — restore the fast path:
php artisan bagisto-api-platform:optimize
```

`bagisto-api-platform:optimize` runs the whole cycle (clear → config:cache → route:cache → warm metadata) in one command. **Never leave the working copy with caches cleared — finish with `:optimize`.** On php-fpm/Octane, reload workers after a deploy so they pick up new code + a fresh schema.

## Playwright e2e

Lives in `packages/Webkul/BagistoApi/tests/e2e-pw/` (`playwright.config.ts`; suites under `tests/restAPI/` and `tests/graphQL/`). Admin auth uses a pre-issued Integration token via the `ADMIN_INTEGRATION_TOKEN` env var (no login flow). See the suite's `TEST_SUITE_OVERVIEW.md`.

## Lint

```bash
./vendor/bin/pint packages/Webkul/BagistoApi
```

Package files are kept comment-free.
