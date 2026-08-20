# @config: Product Type Configuration

## Basic Configuration Structure

The `Config/product-types.php` file is a simple PHP array that registers your product type:

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

## Required Configuration Properties

| Property | Description | Example |
|----------|-------------|---------|
| `key` | Unique identifier (matches array key) | `'subscription'` |
| `name` | Display name in admin dropdown | `'Subscription'` |
| `class` | Full namespace to your product type class | `'Webkul\SubscriptionProduct\Type\Subscription'` |
| `sort` | Order in dropdown (optional, default: 0) | `5` |

## How Bagisto Uses This Configuration

### 1. Admin Product Creation
- Reads all registered product types from configuration
- Shows them in the "Product Type" dropdown
- Uses the `name` for display and `sort` for ordering

### 2. Product Type Instantiation
- Looks up the product's type using the `key`
- Creates an instance of the `class`
- Calls methods on that instance for product behavior

### 3. Configuration Loading
Your service provider merges your configuration:

```php
public function register(): void
{
    $this->mergeConfigFrom(
        dirname(__DIR__) . '/Config/product-types.php',
        'product_types'
    );
}
```

## Multiple Product Types

```php
<?php

return [
    'subscription' => [
        'key'   => 'subscription',
        'name'  => 'Subscription',
        'class' => 'Webkul\SubscriptionProduct\Type\Subscription',
        'sort'  => 5,
    ],
    
    'rental' => [
        'key'   => 'rental',
        'name'  => 'Rental Product',
        'class' => 'Webkul\RentalProduct\Type\Rental',
        'sort'  => 6,
    ],
];
```

---
