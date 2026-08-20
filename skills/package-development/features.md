# Features — Localization, Menus, ACL, System Config

## Localization

Owned by the `coding-standards` skill — see its
[localization.md](../coding-standards/localization.md): 22 locales, `en`
canonical, and `php artisan bagisto:translations:check`.

## DataGrid

Admin listing pages are owned by the **`datagrid-development`** skill — columns
and their types, search/filter/sort flags, dropdown options, closures, joins and
`addFilter`, row and mass actions, ACL gating, export, and the `v-html` XSS
surface every cell carries.

The wiring, in short: a `DataGrid` subclass implements `prepareQueryBuilder()`
and `prepareColumns()` (optionally `prepareActions()` and
`prepareMassActions()`), the controller returns
`datagrid(<Name>DataGrid::class)->process()` on an AJAX request, and the view
renders `<x-admin::datagrid :src="route('…')" />`.

## Admin Menu

### Creating Menu Configuration

**File:** `packages/Webkul/RMA/src/Config/admin-menu.php`

```php
<?php

return [
    [
        'key' => 'rma',
        'name' => 'rma::app.admin.menu.rma',
        'route' => 'admin.rma.return-requests.index',
        'sort' => 100,
        'icon' => 'icon-rma',
    ],
    [
        'key' => 'rma.return-requests',
        'name' => 'rma::app.admin.menu.return-requests',
        'route' => 'admin.rma.return-requests.index',
        'sort' => 1,
    ],
];
```

### Registering Menu

In service provider `register()` method:

```php
$this->mergeConfigFrom(
    dirname(__DIR__) . '/Config/admin-menu.php',
    'menu.admin'
);
```

## Access Control List (ACL)

### Creating ACL Configuration

**File:** `packages/Webkul/RMA/src/Config/acl.php`

```php
<?php

return [
    [
        'key' => 'rma',
        'name' => 'rma::app.admin.acl.rma',
        'route' => 'admin.rma.return-requests.index',
        'sort' => 1,
    ],
    [
        'key' => 'rma.return-requests',
        'name' => 'rma::app.admin.acl.return-requests',
        'route' => 'admin.rma.return-requests.index',
        'sort' => 1,
    ],
    [
        'key' => 'rma.return-requests.view',
        'name' => 'rma::app.admin.acl.view',
        'route' => 'admin.rma.return-requests.show',
        'sort' => 1,
    ],
];
```

### Registering ACL

In service provider `register()` method:

```php
$this->mergeConfigFrom(
    dirname(__DIR__) . '/Config/acl.php',
    'acl'
);
```

### Checking Permissions

```php
// In controller
if (! bouncer()->hasPermission('rma')) {
    abort(401, 'Unauthorized access.');
}
```

```blade
<!-- In Blade -->
@if (bouncer()->hasPermission('rma'))
    <!-- Show content -->
@endif
```

## System Configuration

### Creating Configuration

**File:** `packages/Webkul/RMA/src/Config/system.php`

```php
<?php

return [
    [
        'key' => 'rma',
        'name' => 'rma::app.admin.system.rma',
        'info' => 'rma::app.admin.system.rma-info',
        'sort' => 1,
    ],
    [
        'key' => 'rma.settings',
        'name' => 'rma::app.admin.system.general-settings',
        'info' => 'rma::app.admin.system.general-settings-info',
        'icon' => 'settings/settings.svg',
        'sort' => 1,
    ],
    [
        'key' => 'rma.settings.general',
        'name' => 'rma::app.admin.system.rma-configuration',
        'info' => 'rma::app.admin.system.rma-configuration-info',
        'sort' => 1,
        'fields' => [
            [
                'name' => 'enable',
                'title' => 'rma::app.admin.system.enable-rma',
                'type' => 'boolean',
            ],
            [
                'name' => 'allow_partial_returns',
                'title' => 'rma::app.admin.system.allow-partial-returns',
                'type' => 'boolean',
            ],
            [
                'name' => 'max_return_days',
                'title' => 'rma::app.admin.system.max-return-days',
                'type' => 'number',
                'validation' => 'numeric|min:1',
            ],
            [
                'name' => 'default_status',
                'title' => 'rma::app.admin.system.default-status',
                'type' => 'select',
                'options' => [
                    ['title' => 'Pending', 'value' => 'pending'],
                    ['title' => 'Approved', 'value' => 'approved'],
                ],
            ],
        ],
    ],
];
```

### Registering Configuration

In service provider `register()` method:

```php
$this->mergeConfigFrom(
    dirname(__DIR__) . '/Config/system.php',
    'core'
);
```

### Field Types

| Type | Purpose |
|------|---------|
| `text` | Text input |
| `password` | Password input |
| `number` | Numeric input |
| `boolean` | Enable/disable switch |
| `select` | Dropdown select |
| `multiselect` | Multi-select dropdown |
| `textarea` | Text area |
| `editor` | Rich text editor (TinyMCE) |
| `image` | Image upload |
| `file` | File upload |
| `country` | Country dropdown |
| `state` | State dropdown (depends on country) |
| `color` | Color picker |

### Dependent Fields

```php
[
    'name' => 'enable_policy',
    'title' => 'Enable Return Policy',
    'type' => 'boolean',
], [
    'name' => 'max_return_days',
    'title' => 'Maximum Return Days',
    'type' => 'number',
    'depends' => 'enable_policy:1',  // Show only when enable_policy is 1
],
```

### Using Configuration Values

```php
// In controller
$isEnabled = core()->getConfigData('rma.settings.general.enable');
$maxDays = core()->getConfigData('rma.settings.general.max_return_days');
```

```blade
<!-- In Blade -->
@if (core()->getConfigData('rma.settings.general.enable'))
    <!-- Show RMA content -->
@endif
```

---

# Key Files Reference

| File | Purpose |
|------|---------|
| `src/Providers/ServiceProvider.php` | Main service provider |
| `src/Providers/ModuleServiceProvider.php` | Concord model registration |
| `src/manifest.php` | Package metadata |
| `src/Database/Migrations/` | Migration files |
| `src/Contracts/` | Model contract interfaces |
| `src/Models/` | Eloquent models |
| `src/Models/*Proxy.php` | Concord model proxies |
| `src/Repositories/` | Repository classes |
| `src/Routes/admin-routes.php` | Admin routes |
| `src/Routes/shop-routes.php` | Shop routes |
| `src/Http/Controllers/` | Controllers |
| `src/Resources/views/` | Blade templates |
| `src/Resources/lang/` | Translation files |
| `src/DataGrids/Admin/` | DataGrid classes |
| `src/Config/admin-menu.php` | Menu configuration |
| `src/Config/acl.php` | ACL permissions |
| `src/Config/system.php` | System configuration |

## Common Pitfalls

- Forgetting to run `composer dump-autoload` after adding package
- Not registering service provider in `bootstrap/providers.php`
- Not clearing cache after changes
- Incorrect namespace in PSR-4 autoloading
- Not using package prefix for table names
- Not registering models in ModuleServiceProvider
- Not merging config in service provider
- Using hardcoded text instead of translation keys
- Not checking permissions in controllers/views
