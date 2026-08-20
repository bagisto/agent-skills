# Package Structure & Registration

## Package Structure

### Standard Directory Structure

```
packages/Webkul/{PackageName}/
├── src/
│   ├── Config/
│   │   ├── admin-menu.php
│   │   ├── acl.php
│   │   └── system.php
│   ├── Database/
│   │   ├── Migrations/
│   │   ├── Seeders/
│   │   └── Factories/
│   ├── Http/
│   │   ├── Controllers/
│   │   │   ├── Admin/
│   │   │   └── Shop/
│   │   ├── Middleware/
│   │   └── Requests/
│   ├── Models/
│   │   └── {Package}Proxy.php
│   ├── Repositories/
│   │   └── {Package}Repository.php
│   ├── Resources/
│   │   ├── views/
│   │   └── lang/
│   ├── Providers/
│   │   ├── {Package}ServiceProvider.php
│   │   └── ModuleServiceProvider.php
│   ├── DataGrids/
│   │   └── Admin/
│   └── manifest.php
└── composer.json
```

## Using Package Generator

The generator is a **convenience, not a requirement** — it only scaffolds the files described in
"Manual Setup" below. Skip this section entirely if you would rather create the files yourself, or
if adding a dev dependency to the project needs sign-off first.

### Installation

```bash
composer require --dev bagisto/bagisto-package-generator
```

### Creating a Package

```bash
# If package directory doesn't exist
php artisan package:make Webkul/RMA

# If package directory already exists
php artisan package:make Webkul/RMA --force
```

### Making Models

```bash
php artisan package:make-model ReturnRequest Webkul/RMA
```

### Making Repositories

```bash
php artisan package:make-repository ReturnRequestRepository Webkul/RMA
```

### Making Migrations

```bash
php artisan package:make-migration CreateRmaRequestsTable Webkul/RMA
```

## Manual Setup

### Create Package Directory

```bash
mkdir -p packages/Webkul/RMA/src/Providers
```

### Create Service Provider

**File:** `packages/Webkul/RMA/src/Providers/RMAServiceProvider.php`

```php
<?php

namespace Webkul\RMA\Providers;

use Illuminate\Support\ServiceProvider;

class RMAServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        //
    }
}
```

## Registering Your Package

### Update Composer Autoloader

In root `composer.json`:

```json
{
    "autoload": {
        "psr-4": {
            "Webkul\\RMA\\": "packages/Webkul/RMA/src"
        }
    }
}
```

Then run:

```bash
composer dump-autoload
```

### Register Service Provider

In `bootstrap/providers.php`:

```php
<?php

return [
    App\Providers\AppServiceProvider::class,
    
    // ... other providers ...
    
    Webkul\RMA\Providers\RMAServiceProvider::class,
];
```

### Clear Cache

```bash
php artisan optimize:clear
```

## Service Provider Methods

### Loading Migrations

```php
public function boot(): void
{
    $this->loadMigrationsFrom(__DIR__ . '/../Database/Migrations');
}
```

### Loading Routes

```php
public function boot(): void
{
    $this->loadRoutesFrom(__DIR__ . '/../Routes/admin-routes.php');
    $this->loadRoutesFrom(__DIR__ . '/../Routes/shop-routes.php');
}
```

### Loading Views

```php
public function boot(): void
{
    $this->loadViewsFrom(__DIR__ . '/../Resources/views', 'rma');
}
```

### Loading Translations

```php
public function boot(): void
{
    $this->loadTranslationsFrom(__DIR__ . '/../Resources/lang', 'rma');
}
```

### Merging Config

```php
public function register(): void
{
    $this->mergeConfigFrom(
        dirname(__DIR__) . '/Config/admin-menu.php',
        'menu.admin'
    );

    $this->mergeConfigFrom(
        dirname(__DIR__) . '/Config/acl.php',
        'acl'
    );

    $this->mergeConfigFrom(
        dirname(__DIR__) . '/Config/system.php',
        'core'
    );
}
```

## Concord Model Registration

### Create ModuleServiceProvider

**File:** `packages/Webkul/RMA/src/Providers/ModuleServiceProvider.php`

```php
<?php

namespace Webkul\RMA\Providers;

use Konekt\Concord\BaseModuleServiceProvider;

class ModuleServiceProvider extends BaseModuleServiceProvider
{
    protected $models = [
        \Webkul\RMA\Models\ReturnRequest::class,
    ];
}
```

### Register in concord.php

In `config/concord.php`:

```php
<?php

return [
    'modules' => [
        // Other service providers...
        \Webkul\RMA\Providers\ModuleServiceProvider::class,
    ],
];
```

---
