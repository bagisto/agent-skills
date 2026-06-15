# Removing the bagisto-api package

**Do this only when the client explicitly asks to remove / uninstall the package.** Never uninstall as a side-effect of any other task.

**Confirm scope first.** Ask whether they want to:
- **(a)** just disable / remove the package code, or
- **(b)** also drop the package's database tables and `.env` config (full teardown — destroys stored API keys and tokens).

Default to (a) unless they ask for the full teardown — (b) is irreversible.

## 1. Remove the code

**If installed via Composer:**

```bash
composer remove bagisto/bagisto-api
```

**If installed manually:**

1. Remove the provider line from `bootstrap/providers.php`:
   `Webkul\BagistoApi\Providers\BagistoApiServiceProvider::class`
2. Remove the PSR-4 entry `"Webkul\\BagistoApi\\": "packages/Webkul/BagistoApi/src"` from the root `composer.json` `autoload` block (or, if you used `composer require bagisto/bagisto-api:@dev` against the path repo, `composer remove bagisto/bagisto-api` instead).
3. Delete the package directory:
   ```bash
   rm -rf packages/Webkul/BagistoApi
   ```
4. `composer dump-autoload`

**Optionally** remove the API Platform dependencies if nothing else uses them: `composer remove api-platform/laravel api-platform/graphql api-platform/metadata api-platform/serializer api-platform/state api-platform/jsonld api-platform/hydra api-platform/openapi api-platform/json-schema api-platform/json-api api-platform/documentation`.

## 2. Clear caches (always)

```bash
php artisan optimize:clear
```

The API Platform metadata cache and the `/api/*` routes are removed once the provider is gone. (`bagisto-api-platform:clear-cache` / `:optimize` no longer exist after removal — `optimize:clear` is the right command here.)

## 3. Full teardown only — database + env (DESTRUCTIVE)

Only when the client asked for option (b). **`composer remove` does NOT drop tables** — the package's migrations leave their tables behind. Dropping them deletes stored storefront keys, admin Integration tokens, guest-cart tokens, and the admin API audit log permanently.

Package-owned tables:

| Table | Holds |
|-------|-------|
| `storefront_keys` | Storefront `X-STOREFRONT-KEY` keys |
| `admin_personal_access_tokens` | Admin Integration tokens (+ IP allowlist columns) |
| `cart_tokens` | Guest-cart Bearer tokens |
| `admin_api_audits` | Admin API write audit log |

Drop them only after explicit confirmation, then remove the `STOREFRONT_*` and `API_PLAYGROUND_*` lines from `.env`.

## 4. Verify removal

```bash
php artisan route:list | grep -c 'api/shop\|api/admin'   # expect 0
```

`<APP_URL>/api` should no longer resolve.
