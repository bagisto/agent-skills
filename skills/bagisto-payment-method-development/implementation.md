## Step-by-Step Guide

### Step 1: Create Package Directory Structure

```bash
mkdir -p packages/Webkul/CustomStripePayment/src/{Payment,Config,Providers}
```

### Step 2: Create Payment Method Configuration

**File:** `packages/Webkul/CustomStripePayment/src/Config/payment-methods.php`

```php
<?php

return [
    'custom_stripe_payment' => [
        'code'        => 'custom_stripe_payment',
        'title'       => 'Credit Card (Stripe)',
        'description' => 'Secure credit card payments powered by Stripe',
        'class'       => 'Webkul\CustomStripePayment\Payment\CustomStripePayment',
        'active'      => true,
        'sort'        => 1,
    ],
];
```

#### Configuration Properties Explained

| Property | Type | Purpose | Description |
|----------|------|---------|-------------|
| **`code`** | String | Unique identifier | Must match the array key and be used consistently across your payment method. |
| **`title`** | String | Default display name | Shown to customers during checkout (can be overridden in admin). |
| **`description`** | String | Payment method description | Brief explanation of the payment method. |
| **`class`** | String | Payment class namespace | Full path to your payment processing class. |
| **`active`** | Boolean | Default status | Whether the payment method is enabled by default. |
| **`sort`** | Integer | Display order | Lower numbers appear first in checkout (0 = first). |

> **Note:** The array key (`custom_stripe_payment`) must match the `code` property and be used consistently in your payment class `$code` property, system configuration key path, and route names and identifiers.

### Step 3: Create Payment Class

**File:** `packages/Webkul/CustomStripePayment/src/Payment/CustomStripePayment.php`

```php
<?php

namespace Webkul\CustomStripePayment\Payment;

use Webkul\Payment\Payment\Payment;

class CustomStripePayment extends Payment
{
    /**
     * Payment method code - must match payment-methods.php key.
     *
     * @var string
     */
    protected $code = 'custom_stripe_payment';

    /**
     * Get redirect URL for payment processing.
     *
     * Note: You need to create this route in your Routes/web.php file
     * or return null if you don't need a redirect.
     *
     * @return string|null
     */
    public function getRedirectUrl()
    {
        // return route('custom_stripe_payment.process');
        return null; // No redirect needed for this basic example
    }

    /**
     * Get additional details for frontend display.
     *
     * @return array
     */
    public function getAdditionalDetails()
    {
        return [
            'title' => $this->getConfigData('title'),
            'description' => $this->getConfigData('description'),
            'requires_card_details' => true,
        ];
    }

    /**
     * Get payment method configuration data.
     *
     * @param  string  $field
     * @return mixed
     */
    public function getConfigData($field)
    {
        return core()->getConfigData('sales.payment_methods.custom_stripe_payment.' . $field);
    }
}
```

### Step 4: Create System Configuration

**File:** `packages/Webkul/CustomStripePayment/src/Config/system.php`

```php
<?php

return [
    [
        'key'    => 'sales.payment_methods.custom_stripe_payment',
        'name'   => 'Custom Stripe Payment',
        'info'   => 'Custom Stripe Payment Method Configuration',
        'sort'   => 1,
        'fields' => [
            [
                'name'          => 'active',
                'title'         => 'Status',
                'type'          => 'boolean',
                'default_value' => true,
                'channel_based' => true,
            ],
            [
                'name'          => 'title',
                'title'         => 'Title',
                'type'          => 'text',
                'default_value' => 'Credit Card (Stripe)',
                'channel_based' => true,
                'locale_based'  => true,
            ],
            [
                'name'          => 'description',
                'title'         => 'Description',
                'type'          => 'textarea',
                'default_value' => 'Secure credit card payments',
                'channel_based' => true,
                'locale_based'  => true,
            ],
            [
                'name'          => 'sort',
                'title'         => 'Sort Order',
                'type'          => 'text',
                'default_value' => '1',
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

**File:** `packages/Webkul/CustomStripePayment/src/Providers/CustomStripePaymentServiceProvider.php`

```php
<?php

namespace Webkul\CustomStripePayment\Providers;

use Illuminate\Support\ServiceProvider;

class CustomStripePaymentServiceProvider extends ServiceProvider
{
    /**
     * Register services.
     *
     * @return void
     */
    public function register(): void
    {
        // Merge payment method configuration.
        $this->mergeConfigFrom(
            dirname(__DIR__) . '/Config/payment-methods.php',
            'payment_methods'
        );

        // Merge system configuration.
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
            "Webkul\\CustomStripePayment\\": "packages/Webkul/CustomStripePayment/src"
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

    Webkul\CustomStripePayment\Providers\CustomStripePaymentServiceProvider::class,
];
```

4. **Clear caches:**

```bash
php artisan optimize:clear
```
