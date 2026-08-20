# Localization

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
