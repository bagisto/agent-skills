## Creating Shop Theme Package

### Goal: Complete Self-Contained Package

The end result should be a complete package with:
- All views inside the package
- All assets inside the package
- Service provider for publishing
- Vite configuration for asset compilation

### Step 1: Create Package Structure

```bash
mkdir -p packages/Webkul/CustomTheme/src/{Providers,Resources/views}
```

### Step 2: Copy Complete Shop Assets

Copy all shop assets to your package to have full control:

```bash
# Copy complete shop assets folder
cp -r packages/Webkul/Shop/src/Resources/assets/* packages/Webkul/CustomTheme/src/Resources/assets/

# Copy complete shop views folder
cp -r packages/Webkul/Shop/src/Resources/views/* packages/Webkul/CustomTheme/src/Resources/views/

# Copy shop package.json for dependencies
cp packages/Webkul/Shop/package.json packages/Webkul/CustomTheme/
```

This gives you:
- Complete CSS foundation with Tailwind
- All JavaScript functionality
- Shop components and layouts
- Images, fonts, and static assets
- Complete Blade template structure
- Dependencies for asset compilation

### Step 3: Add Custom Home Page (Boilerplate)

After copying, create a custom home page to show it's a new theme:

**File:** `packages/Webkul/CustomTheme/src/Resources/views/home/index.blade.php`

```blade
<x-shop::layouts>
    <x-slot:title>
        Custom Theme Home
    </x-slot>

    {{-- Hero Section --}}
    <div class="hero-section bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20">
        <div class="container mx-auto px-4 text-center">
            <h1 class="text-5xl font-bold mb-6">
                Welcome to Our Store
            </h1>
            
            <p class="text-xl mb-8 opacity-90">
                Professional theme with modern design
            </p>
            
            <a href="{{ route('shop.search.index') }}" 
               class="bg-white text-blue-600 font-bold py-3 px-8 rounded-lg hover:bg-gray-100 transition duration-300">
                Start Shopping
            </a>
        </div>
    </div>

    {{-- Featured Products --}}
    <div class="container mx-auto px-4 py-16">
        <h2 class="text-3xl font-bold text-center mb-12">
            Featured Products
        </h2>
        
        <!-- Product grid -->
    </div>
</x-shop::layouts>
```

### Step 4: Create Custom Layout (Optional)

Create your own master layout for complete control:

**File:** `packages/Webkul/CustomTheme/src/Resources/views/layouts/master.blade.php`

```blade
<!DOCTYPE html>
<html lang="{{ app()->getLocale() }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ $title ?? config('app.name') }}</title>
    
    {{-- Load theme assets manually --}}
    @bagistoVite([
        'src/Resources/assets/css/app.css',
        'src/Resources/assets/js/app.js'
    ])
    
    @stack('meta')
    @stack('styles')
</head>
<body class="{{ $bodyClass ?? '' }}">
    @if($hasHeader ?? true)
        @include('custom-theme::layouts.header')
    @endif
    
    <main class="main-content">
        {{ $slot }}
    </main>
    
    @if($hasFooter ?? true)
        @include('custom-theme::layouts.footer')
    @endif
    
    @stack('scripts')
</body>
</html>
```

### Step 5: Create Service Provider

**File:** `packages/Webkul/CustomTheme/src/Providers/CustomThemeServiceProvider.php`

```php
<?php

namespace Webkul\CustomTheme\Providers;

use Illuminate\Support\ServiceProvider;

class CustomThemeServiceProvider extends ServiceProvider
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
        // Publish views to resources/themes/custom-theme/views
        $this->publishes([
            __DIR__ . '/../Resources/views' => resource_path('themes/custom-theme/views'),
        ], 'custom-theme-views');
    }
}
```

### Step 6: Configure Autoloading

Update `composer.json`:

```json
"autoload": {
    "psr-4": {
        "Webkul\\CustomTheme\\": "packages/Webkul/CustomTheme/src"
    }
}
```

Run: `composer dump-autoload`

### Step 7: Register Service Provider

Add to `bootstrap/providers.php`:

```php
Webkul\CustomTheme\Providers\CustomThemeServiceProvider::class,
```

### Step 8: Update Theme Configuration

**File:** `config/themes.php`

```php
'shop-default' => 'custom-theme',

'shop' => [
    'default' => [
        'name' => 'Default',
        'assets_path' => 'public/themes/shop/default',
        'views_path' => 'resources/themes/default/views',
        'vite' => [
            'hot_file' => 'shop-default-vite.hot',
            'build_directory' => 'themes/shop/default/build',
            'package_assets_directory' => 'src/Resources/assets',
        ],
    ],
    'custom-theme' => [
        'name' => 'Custom Theme Package',
        'assets_path' => 'public/themes/shop/custom-theme',
        'views_path' => 'resources/themes/custom-theme/views',
        'vite' => [
            'hot_file' => 'custom-theme-vite.hot',
            'build_directory' => 'themes/custom-theme/build',
            'package_assets_directory' => 'src/Resources/assets',
        ],
    ],
],
```

### Step 9: Publish Views

```bash
php artisan vendor:publish --provider="Webkul\CustomTheme\Providers\CustomThemeServiceProvider"
```

### Step 10: Clear Cache

```bash
php artisan optimize:clear
```

### Step 11: Activate Theme

1. Login to admin panel
2. Go to Settings → Channels
3. Edit channel and select your theme
4. Save

### Step 12: Build Assets

```bash
# Navigate to package
cd packages/Webkul/CustomTheme

# Install dependencies
npm install

# Build assets for production
npm run build
```

This will compile your theme assets and create the build directory. After building, your custom theme will be ready to use with the custom home page you created.
