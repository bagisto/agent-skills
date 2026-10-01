# Localization

### Naming Keys

**Every segment of a translation key is kebab-case** — `eu-withdrawal.view.received-at`, never
`eu_withdrawal.view.received_at` and never `receivedAt`. This holds at every level of the nested
array, in all 22 locales.

A key that mirrors an identifier is still kebab-case; adapt the lookup rather than the key. The
Elasticsearch auth types are the worked example — the enum keeps the values it has already written to
`core_config`, and the option builder maps them onto the key:

```php
'title' => 'admin::app.configuration.index.search-engines.elastic.settings.auth-types.'
    .str_replace('_', '-', $auth->value),
```

Two exceptions, both because the segment is **data rather than a name**: currency codes
(`seeders.core.currencies.AED`) and locale codes (`pt_BR`) keep their own casing.

Where a key is built by concatenation, rename the literal prefix along with the key it points at, and
keep the runtime suffix a valid segment:

```blade
@lang('shop::app.eu-withdrawal.confirmation.intro-'.$withdrawal->status)
```

**Do not confuse this with route names, which are snake_case.** The same feature is
`admin.sales.eu_withdrawals.index` as a route and `admin::app.eu-withdrawal.…` as a translation key,
so never rename one by searching for the other's spelling.

### Creating Translation Files

**File:** `packages/Webkul/RMA/src/Resources/lang/en/app.php`

```php
<?php

return [
    'admin' => [
        'return-requests' => [
            'title' => 'RMA Listing',
            'datagrid' => [
                'id' => 'ID',
                'product-name' => 'Product Name',
                'status' => 'Status',
                'view' => 'View',
            ],
        ],
    ],
];
```

### Loading Translations

In service provider `boot()` method:

```php
$this->loadTranslationsFrom(__DIR__ . '/../Resources/lang', 'rma');
```

### Using Translations

```blade
<!-- In Blade templates -->
@lang('rma::app.admin.return-requests.title')
```

```php
// In controllers/code
trans('rma::app.admin.return-requests.title')
__('rma::app.admin.return-requests.title')
```

### Publishing Translations (Optional)

```php
public function boot(): void
{
    $this->publishes([
        __DIR__ . '/../Resources/lang' => resource_path('lang/vendor/rma'),
    ], 'rma-translations');
}
```

Users can then run:
```bash
php artisan vendor:publish --tag=rma-translations
```
