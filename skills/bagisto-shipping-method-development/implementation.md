## Step-by-Step Guide

### Step 1: Create Package Directory Structure

```bash
mkdir -p packages/Webkul/CustomExpressShipping/src/{Carriers,Config,Providers}
```

### Step 2: Create Carrier Configuration

**File:** `packages/Webkul/CustomExpressShipping/src/Config/carriers.php`

```php
<?php

return [
    'custom_express_shipping' => [
        'code'         => 'custom_express_shipping',
        'title'        => 'Express Delivery (1-2 Days)',
        'description'  => 'Premium express shipping with tracking',
        'active'       => true,
        'default_rate' => '19.99',
        'type'         => 'per_order',
        'class'        => 'Webkul\CustomExpressShipping\Carriers\CustomExpressShipping',
    ],
];
```

#### Configuration Properties Explained

| Property | Type | Purpose | Description |
|----------|------|---------|-------------|
| **`code`** | String | Unique identifier | Must match the array key and `$code` property in carrier class. |
| **`title`** | String | Default display name | Shown to customers during checkout (can be overridden in admin). |
| **`description`** | String | Method description | Brief explanation of the shipping service. |
| **`active`** | Boolean | Default status | Whether the shipping method is enabled by default. |
| **`default_rate`** | String/Float | Base shipping cost | Base shipping cost before calculations. |
| **`type`** | String | Pricing model | `per_order` (flat rate) or `per_unit` (per item). |
| **`class`** | String | Carrier class namespace | Full path to your carrier class. |

> **Note:** The array key (`custom_express_shipping`) must match the `code` property in your carrier class, system configuration key path, and should be consistent throughout.

### Step 3: Create Carrier Class

**File:** `packages/Webkul/CustomExpressShipping/src/Carriers/CustomExpressShipping.php`

```php
<?php

namespace Webkul\CustomExpressShipping\Carriers;

use Webkul\Shipping\Carriers\AbstractShipping;
use Webkul\Checkout\Models\CartShippingRate;
use Webkul\Checkout\Facades\Cart;

class CustomExpressShipping extends AbstractShipping
{
    /**
     * Shipping method code - must match carriers.php key.
     *
     * @var string
     */
    protected $code = 'custom_express_shipping';

    /**
     * Shipping method code.
     *
     * @var string
     */
    protected $method = 'custom_express_shipping_custom_express_shipping';

    /**
     * Calculate shipping rate for the current cart.
     *
     * @return \Webkul\Checkout\Models\CartShippingRate|false
     */
    public function calculate()
    {
        if (! $this->isAvailable()) {
            return false;
        }

        return $this->getRate();
    }

    /**
     * Get shipping rate.
     *
     * @return \Webkul\Checkout\Models\CartShippingRate
     */
    public function getRate(): CartShippingRate
    {
        $cart = Cart::getCart();

        $cartShippingRate = new CartShippingRate;

        $cartShippingRate->carrier = $this->getCode();
        $cartShippingRate->carrier_title = $this->getConfigData('title');
        $cartShippingRate->method = $this->getMethod();
        $cartShippingRate->method_title = $this->getConfigData('title');
        $cartShippingRate->method_description = $this->getConfigData('description');
        $cartShippingRate->price = 0;
        $cartShippingRate->base_price = 0;

        $baseRate = (float) $this->getConfigData('default_rate');

        if ($this->getConfigData('type') == 'per_unit') {
            foreach ($cart->items as $item) {
                if ($item->getTypeInstance()->isStockable()) {
                    $cartShippingRate->price += core()->convertPrice($baseRate) * $item->quantity;
                    $cartShippingRate->base_price += $baseRate * $item->quantity;
                }
            }
        } else {
            $cartShippingRate->price = core()->convertPrice($baseRate);
            $cartShippingRate->base_price = $baseRate;
        }

        return $cartShippingRate;
    }
}
```

### Step 4: Create System Configuration

**File:** `packages/Webkul/CustomExpressShipping/src/Config/system.php`

```php
<?php

return [
    [
        'key'    => 'sales.carriers.custom_express_shipping',
        'name'   => 'Custom Express Shipping',
        'info'   => 'Configure the Custom Express Shipping method settings.',
        'sort'   => 1,
        'fields' => [
            [
                'name'          => 'title',
                'title'         => 'Method Title',
                'type'          => 'text',
                'validation'    => 'required',
                'channel_based' => true,
                'locale_based'  => true,
            ],
            [
                'name'          => 'description',
                'title'         => 'Description',
                'type'          => 'textarea',
                'channel_based' => true,
                'locale_based'  => false,
            ],
            [
                'name'          => 'default_rate',
                'title'         => 'Base Rate',
                'type'          => 'text',
                'validation'    => 'required|numeric|min:0',
                'channel_based' => true,
                'locale_based'  => false,
            ],
            [
                'name'          => 'type',
                'title'         => 'Pricing Type',
                'type'          => 'select',
                'options'       => [
                    [
                        'title' => 'Per Order (Flat Rate)',
                        'value' => 'per_order',
                    ],
                    [
                        'title' => 'Per Item',
                        'value' => 'per_unit',
                    ],
                ],
                'channel_based' => true,
                'locale_based'  => false,
            ],
            [
                'name'          => 'active',
                'title'         => 'Enabled',
                'type'          => 'boolean',
                'validation'    => 'required',
                'channel_based' => true,
                'locale_based'  => false,
            ],
        ],
    ],
];
```

#### System Configuration Field Properties

| Property | Purpose | Description |
|----------|---------|-------------|
| **`name`** | Field identifier | Used to store and retrieve configuration values. |
| **`title`** | Field label | Label displayed in the admin form. |
| **`type`** | Input type | `text`, `textarea`, `boolean`, `select`, `password`, etc. |
| **`default_value`** | Default setting | Initial value when first configured. |
| **`channel_based`** | Multi-store support | Different values per sales channel. |
| **`locale_based`** | Multi-language support | Translatable content per language. |
| **`validation`** | Field validation | Rules like `required`, `numeric`, `email`. |

### Step 5: Create Service Provider

**File:** `packages/Webkul/CustomExpressShipping/src/Providers/CustomExpressShippingServiceProvider.php`

```php
<?php

namespace Webkul\CustomExpressShipping\Providers;

use Illuminate\Support\ServiceProvider;

class CustomExpressShippingServiceProvider extends ServiceProvider
{
    /**
     * Register services.
     *
     * @return void
     */
    public function register(): void
    {
        $this->mergeConfigFrom(
            dirname(__DIR__) . '/Config/carriers.php',
            'carriers'
        );

        $this->mergeConfigFrom(
            dirname(__DIR__) . '/Config/system.php',
            'core'
        );
    }

    /**
     * Bootstrap services.
     *
     * @return void
     */
    public function boot(): void
    {
        //
    }
}
```

### Step 6: Register Your Package

1. **Add to composer.json** (in Bagisto root directory):

```json
{
    "autoload": {
        "psr-4": {
            "Webkul\\CustomExpressShipping\\": "packages/Webkul/CustomExpressShipping/src"
        }
    }
}
```

2. **Update autoloader:**

```bash
composer dump-autoload
```

3. **Register service provider** in `bootstrap/providers.php`:

```php
<?php

return [
    App\Providers\AppServiceProvider::class,

    // ... other providers ...

    Webkul\CustomExpressShipping\Providers\CustomExpressShippingServiceProvider::class,
];
```

4. **Clear caches:**

```bash
php artisan optimize:clear
```
