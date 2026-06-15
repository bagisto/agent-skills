# Installing the bagisto-api package

**Do this only when the client explicitly asks to install / set up the API.** Never trigger an install just because you detected the package or a Bagisto project.

## 0. Prerequisites

- PHP **8.3+**, Composer 2, MySQL 8.0+ (or PostgreSQL 14+).
- **Bagisto v2.3.8** already installed and serving (the version the package is tested against in CI).
- The package's API Platform dependencies are pinned to a consistent set (`api-platform/laravel v4.1.25`, `api-platform/graphql v4.2.3`, the core `api-platform/*` components `v4.3.1`) and resolve automatically on `composer require`.

### Is Bagisto already here?

Run from the intended project root:

```bash
if [ -f artisan ] && grep -q '"bagisto/bagisto"' composer.json 2>/dev/null; then
  echo "BAGISTO_PRESENT"   # skip to step 1
else
  echo "BAGISTO_ABSENT"    # install Bagisto 2.3.8 first
fi
```

If absent, install Bagisto first (`composer create-project bagisto/bagisto:2.3.8 .` then the interactive `php artisan bagisto:install`), **then** install the package. If present, go straight to step 1. **Never print or imply a Bagisto/API version-mismatch warning — the API layer is version-independent against a 2.3.x base.**

## 1. Ask the client: which install method?

| Method | Source | Stability | Use when |
|--------|--------|-----------|----------|
| **Composer (recommended, quick start)** | `composer require bagisto/bagisto-api` (latest tagged release) | **Stable** | Client wants the proven release. |
| **Manual** | Download/extract the package into `packages/Webkul/BagistoApi/` and wire it by hand | Gives more control; lets you track the **newest (`main`)** code ahead of the stable tag | Client wants full control or the newest features. |

**Default to Composer unless the client picks Manual.** State the trade-off in one line: *Composer = proven stable release; Manual = full control / newest code, more wiring.*

## 2A. Composer install (recommended)

```bash
composer require bagisto/bagisto-api
php artisan bagisto-api-platform:install
```

That's it — `bagisto-api-platform:install` configures API Platform for Bagisto (the package's service provider is auto-discovered via its `extra.laravel.providers`). Continue to step 3.

## 2B. Manual install

**Step 1 — place the files.** Download the package from `https://github.com/bagisto/bagisto-api` and extract it to `packages/Webkul/BagistoApi/`.

**Step 2 — register the service provider** in `bootstrap/providers.php`:

```php
return [
    // ...existing providers...
    Webkul\BagistoApi\Providers\BagistoApiServiceProvider::class,
];
```

**Step 3 — add PSR-4 autoload** in the project's root `composer.json`:

```json
{
  "autoload": {
    "psr-4": {
      "Webkul\\BagistoApi\\": "packages/Webkul/BagistoApi/src"
    }
  }
}
```

> Note: the default Bagisto root `composer.json` already declares a `path` repository for `packages/*/*`. If you prefer, you can instead `composer require bagisto/bagisto-api:@dev` to let Composer resolve the local path package (which auto-registers the provider) rather than editing `bootstrap/providers.php` + the autoload block. Either approach works — the file-drop method above is the package's documented one.

**Step 4 — install the pinned API Platform dependencies:**

```bash
composer require \
  api-platform/laravel:v4.1.25 \
  api-platform/graphql:v4.2.3 \
  api-platform/metadata:v4.3.1 \
  api-platform/serializer:v4.3.1 \
  api-platform/state:v4.3.1 \
  api-platform/jsonld:v4.3.1 \
  api-platform/hydra:v4.3.1 \
  api-platform/openapi:v4.3.1 \
  api-platform/json-schema:v4.3.1 \
  api-platform/json-api:v4.3.1 \
  api-platform/documentation:v4.3.1
```

**Step 5 — run the installer + autoload:**

```bash
composer dump-autoload
php artisan bagisto-api-platform:install
```

**Step 6 — set the `.env` storefront vars:**

```
STOREFRONT_DEFAULT_RATE_LIMIT=100
STOREFRONT_CACHE_TTL=60
STOREFRONT_KEY_PREFIX=storefront_key_
STOREFRONT_PLAYGROUND_KEY=pk_storefront_xxxxxxxxxxxxxxxxxxxxxxxxxx
API_PLAYGROUND_AUTO_INJECT_STOREFRONT_KEY=true
```

## 3. Issue credentials

**Storefront key** (for `/api/shop/*` — sent as `X-STOREFRONT-KEY`):

```bash
php artisan bagisto-api:generate-key
```

(`php artisan bagisto-api:key:manage` handles rotation / expiry / lifecycle.)

**Admin Integration token** (for `/api/admin/*` — sent as `Authorization: Bearer <id>|<token>`): created in the **admin panel**, not the CLI:

1. Enable the module: **Configuration → API → Integration → Module Settings → Enabled** (otherwise the menu stays hidden).
2. **Settings → Integration → Create** — name, assigned admin, permission mode (`All` / `Custom` / `Same as Web`), optional IP allowlist, rate limits, expiry → save as draft.
3. **Generate** — the plaintext token shows **once**; copy it immediately. Lost tokens can only be **Regenerated**.

Each token is scoped to one admin and capped by that admin's role permissions; one active token per admin.

## 4. Optimise (always finish here)

```bash
php artisan bagisto-api-platform:optimize
```

This clears stale caches, rebuilds the config + route caches, and pre-warms the API Platform metadata cache so no request pays the per-request route rebuild or the cold-start metadata build. **Run it after every install, package update, or endpoint change.**

## 5. Verify

Access points once installed:

- API landing: `<APP_URL>/api`
- REST docs: `<APP_URL>/api/shop/docs` · `<APP_URL>/api/admin/docs`
- GraphQL playground: `<APP_URL>/api/graphiql` (shop) · `<APP_URL>/api/admin/graphiql` (admin)

Smoke-test an authenticated admin call:

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer <id>|<token>" <APP_URL>/api/admin/get
# expect 200
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Routes 404 right after install | `php artisan optimize:clear && php artisan bagisto-api-platform:clear-cache`, then `php artisan bagisto-api-platform:optimize`. |
| Slow responses | `php artisan bagisto-api-platform:optimize` (route+config cache + metadata warm). Never leave caches cleared. |
| Provider not found (manual) | Confirm the `bootstrap/providers.php` line + the PSR-4 autoload entry, then `composer dump-autoload`. |
| Admin call returns 401 | Token isn't active / the module is disabled / wrong `Bearer <id>|<token>` format. |
| Shop call returns 401 `missing_key` | Send the `X-STOREFRONT-KEY` header; generate one with `bagisto-api:generate-key`. |
