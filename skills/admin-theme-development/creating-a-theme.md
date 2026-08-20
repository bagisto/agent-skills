## Creating Admin Theme Package

### Goal: Complete Self-Contained Package

The end result should be a complete package with:
- All views inside the package
- All assets inside the package
- Service provider for publishing
- Vite configuration for asset compilation

### Step 1: Create Package Structure

```bash
mkdir -p packages/Webkul/CustomAdminTheme/src/{Providers,Resources/views}
```

### Step 2: Copy Complete Admin Assets

Copy all admin assets to your package to have full control:

```bash
# Copy complete admin assets folder
cp -r packages/Webkul/Admin/src/Resources/assets/* packages/Webkul/CustomAdminTheme/src/Resources/assets/

# Copy complete admin views folder
cp -r packages/Webkul/Admin/src/Resources/views/* packages/Webkul/CustomAdminTheme/src/Resources/views/

# Copy admin package.json for dependencies
cp packages/Webkul/Admin/package.json packages/Webkul/CustomAdminTheme/
```

This gives you:
- Complete CSS foundation with Tailwind
- All JavaScript functionality
- Admin components and layouts
- Images, fonts, and static assets
- Complete Blade template structure
- Dependencies for asset compilation

### Step 3: Add Custom Dashboard Page (Boilerplate)

After copying, create a custom dashboard page to show it's a new theme:

**File:** `packages/Webkul/CustomAdminTheme/src/Resources/views/dashboard/index.blade.php`

```blade
<x-admin::layouts>
    <x-slot:title>
        Custom Admin Dashboard
    </x-slot>

    <div class="flex gap-4 justify-between max-sm:flex-wrap">
        <h1 class="py-[11px] text-xl text-gray-800 dark:text-white font-bold">
            Custom Theme Dashboard
        </h1>

        <div class="flex gap-x-2.5 items-center">
            <button class="secondary-button">
                Reset to Defaults
            </button>
            
            <button class="primary-button">
                Save Settings
            </button>
        </div>
    </div>

    {{-- Dashboard Content --}}
    <div class="mt-8 bg-white dark:bg-gray-900 rounded-lg shadow p-6">
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white mb-6">
            Welcome to Custom Admin Theme
        </h1>
        
        <p class="text-lg text-gray-600 dark:text-gray-300 mb-8">
            Your customized Bagisto admin panel!
        </p>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h3 class="text-xl font-semibold text-blue-800 mb-2">
                    Analytics
                </h3>
                <p class="text-blue-600">
                    Enhanced dashboard analytics and reporting
                </p>
            </div>
            
            <div class="bg-green-50 p-4 rounded-lg border border-green-200">
                <h3 class="text-xl font-semibold text-green-800 mb-2">
                    Orders
                </h3>
                <p class="text-green-600">
                    Streamlined order management interface
                </p>
            </div>
            
            <div class="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <h3 class="text-xl font-semibold text-purple-800 mb-2">
                    Customers
                </h3>
                <p class="text-purple-600">
                    Enhanced customer management tools
                </p>
            </div>
        </div>
    </div>
</x-admin::layouts>
```

### Step 4: Create Custom Layout (Optional)

Create your own master layout for complete control:

**File:** `packages/Webkul/CustomAdminTheme/src/Resources/views/layouts/master.blade.php`

```blade
<!DOCTYPE html>
<html lang="{{ app()->getLocale() }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ $title ?? config('app.name') }}</title>
    
    {{-- Load assets manually for custom layouts --}}
    @bagistoVite([
        'src/Resources/assets/css/app.css',
        'src/Resources/assets/js/app.js'
    ])
</head>
<body class="dark:bg-gray-900">
    {{-- Custom sidebar --}}
    @include('custom-admin-theme::layouts.sidebar')
    
    <div class="flex">
        {{-- Main content area --}}
        <main class="flex-1 p-6">
            {{ $slot }}
        </main>
    </div>
</body>
</html>
```

### Step 5: Create Service Provider

**File:** `packages/Webkul/CustomAdminTheme/src/Providers/CustomAdminThemeServiceProvider.php`

```php
<?php

namespace Webkul\CustomAdminTheme\Providers;

use Illuminate\Support\ServiceProvider;

class CustomAdminThemeServiceProvider extends ServiceProvider
{
    /**
     * Register services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap services.
     */
    public function boot(): void
    {
        // Publish views to resources/admin-themes/custom-admin-theme/views
        $this->publishes([
            __DIR__ . '/../Resources/views' => resource_path('admin-themes/custom-admin-theme/views'),
        ], 'custom-admin-theme-views');
    }
}
```

### Step 6: Configure Autoloading

Update `composer.json`:

```json
"autoload": {
    "psr-4": {
        "Webkul\\CustomAdminTheme\\": "packages/Webkul/CustomAdminTheme/src"
    }
}
```

Run: `composer dump-autoload`

### Step 7: Register Service Provider

Add to `bootstrap/providers.php`:

```php
Webkul\CustomAdminTheme\Providers\CustomAdminThemeServiceProvider::class,
```

### Step 8: Update Theme Configuration

**File:** `config/themes.php`

```php
'admin-default' => 'custom-admin-theme',

'admin' => [
    'default' => [
        'name' => 'Default',
        'assets_path' => 'public/themes/admin/default',
        'views_path' => 'resources/admin-themes/default/views',
        'vite' => [
            'hot_file' => 'admin-default-vite.hot',
            'build_directory' => 'themes/admin/default/build',
            'package_assets_directory' => 'src/Resources/assets',
        ],
    ],
    'custom-admin-theme' => [
        'name' => 'Custom Admin Theme',
        'assets_path' => 'public/themes/admin/custom-admin-theme',
        'views_path' => 'resources/admin-themes/custom-admin-theme/views',
        'vite' => [
            'hot_file' => 'admin-custom-vite.hot',
            'build_directory' => 'themes/admin/custom-admin/build',
            'package_assets_directory' => 'src/Resources/assets',
        ],
    ],
],
```

### Step 9: Publish Views

```bash
php artisan vendor:publish --provider="Webkul\CustomAdminTheme\Providers\CustomAdminThemeServiceProvider"
```

### Step 10: Clear Cache

```bash
php artisan optimize:clear
```

### Step 11: Build Assets

```bash
# Navigate to package
cd packages/Webkul/CustomAdminTheme

# Install dependencies
npm install

# Build assets for production
npm run build
```

This will compile your admin theme assets and create the build directory. After building, your custom admin theme will be ready to use with the custom dashboard you created.
