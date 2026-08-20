# @build: Complete Subscription Implementation

## Package Structure

```
packages/Webkul/SubscriptionProduct/
└── src/
    ├── Type/
    │   └── Subscription.php
    ├── Config/
    │   └── product-types.php
    └── Providers/
        └── SubscriptionServiceProvider.php
```

## Step 1: Create Package Structure

```bash
mkdir -p packages/Webkul/SubscriptionProduct/src/{Type,Config,Providers}
```

## Step 2: Configure Product Type

**File:** `packages/Webkul/SubscriptionProduct/src/Config/product-types.php`

```php
<?php

return [
    'subscription' => [
        'key'   => 'subscription',
        'name'  => 'Subscription',
        'class' => 'Webkul\SubscriptionProduct\Type\Subscription',
        'sort'  => 5,
    ],
];
```

## Step 3: Create Product Type Class

**File:** `packages/Webkul/SubscriptionProduct/src/Type/Subscription.php`

```php
<?php

namespace Webkul\SubscriptionProduct\Type;

use Webkul\Product\Helpers\Indexers\Price\Simple as SimpleIndexer;
use Webkul\Product\Type\AbstractType;

class Subscription extends AbstractType
{
    public function getPriceIndexer()
    {
        return app(SimpleIndexer::class);
    }
    
    public function isStockable(): bool
    {
        return false;
    }
    
    public function showQuantityBox(): bool
    {
        return true;
    }
    
    public function isSaleable(): bool
    {
        if (! parent::isSaleable()) {
            return false;
        }
        
        return true;
    }
    
    public function haveSufficientQuantity(int $qty): bool
    {
        return true;
    }
    
    public function totalQuantity(): int
    {
        return $this->product->subscription_slots ?? 0;
    }
    
    public function prepareForCart(array $data): array
    {
        if (empty($data['subscription_frequency'])) {
            return 'Please select subscription frequency.';
        }
        
        $cartData = parent::prepareForCart($data);
        
        $cartData[0]['additional']['subscription_frequency'] = $data['subscription_frequency'];
        $cartData[0]['additional']['subscription_start_date'] = $data['start_date'] ?? now()->addDays(1)->format('Y-m-d');
        
        return $cartData;
    }
}
```

## Step 4: Create Service Provider

**File:** `packages/Webkul/SubscriptionProduct/src/Providers/SubscriptionServiceProvider.php`

```php
<?php

namespace Webkul\SubscriptionProduct\Providers;

use Illuminate\Support\ServiceProvider;

class SubscriptionServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->mergeConfigFrom(
            dirname(__DIR__) . '/Config/product-types.php',
            'product_types'
        );
    }

    public function boot(): void
    {
        //
    }
}
```

## Step 5: Register Your Package

### Update composer.json

```json
{
    "autoload": {
        "psr-4": {
            "Webkul\\SubscriptionProduct\\": "packages/Webkul/SubscriptionProduct/src"
        }
    }
}
```

### Update autoloader

```bash
composer dump-autoload
```

### Register service provider

In `bootstrap/providers.php`:

```php
<?php

return [
    App\Providers\AppServiceProvider::class,
    
    // ... other providers ...
    
    Webkul\SubscriptionProduct\Providers\SubscriptionServiceProvider::class,
];
```

### Clear cache

```bash
php artisan optimize:clear
```

## Testing

```bash
php artisan tinker

# Test product type
>>> $product = \Webkul\Product\Models\Product::where('type', 'subscription')->first()
>>> $subscription = $product->getTypeInstance()

# Test methods
>>> $subscription->isStockable()        // Should return false
>>> $subscription->showQuantityBox()    // Should return true
>>> $subscription->isSaleable()         // Should return true

# Test cart preparation
>>> $cartData = $subscription->prepareForCart(['quantity' => 2, 'subscription_frequency' => 'monthly'])
>>> $cartData[0]['additional']  // Should show subscription data
```

## Built-in Product Types Reference

| Type | Use Case | Key Features |
|------|----------|--------------|
| **Simple** | Basic products | Standard pricing, inventory tracking |
| **Configurable** | Products with variations | Variant management, attribute-based pricing |
| **Virtual** | Non-physical products | No shipping required |
| **Grouped** | Related products sold together | Bundle pricing, component selection |

## Key Files Reference

| File | Purpose |
|------|---------|
| `Config/product-types.php` | Product type registration |
| `Type/ProductType.php` | Product type class |
| `Providers/ServiceProvider.php` | Package registration |
| `packages/Webkul/Product/src/Type/AbstractType.php` | Base class |

## Common Pitfalls

- Forgetting to merge config in service provider
- Not matching `$key` with array key in configuration
- Not registering service provider in `bootstrap/providers.php`
- Forgetting to run `composer dump-autoload` after adding package
- Not clearing cache after configuration changes
- Forgetting to call `parent::isSaleable()` when overriding
- Not handling cart data correctly in `prepareForCart()`
