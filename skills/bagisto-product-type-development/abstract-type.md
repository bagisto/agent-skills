# @abstract: AbstractType Methods

## AbstractType Overview

Every product type in Bagisto extends the `AbstractType` class:

```php
<?php

namespace Webkul\Product\Type;

abstract class AbstractType
{
    protected $product;
    protected $isStockable = true;
    protected $showQuantityBox = false;
    protected $haveSufficientQuantity = true;
    protected $canBeMovedFromWishlistToCart = true;
    protected $additionalViews = [];
    protected $skipAttributes = [];
}
```

## Key Methods to Override

### Product Availability Control

#### `isSaleable(): bool`

Controls whether the product appears as purchasable:

```php
public function isSaleable(): bool
{
    if (! parent::isSaleable()) {
        return false;
    }
    
    // Add custom availability logic
    return true;
}
```

#### `haveSufficientQuantity(int $qty): bool`

Checks if enough quantity is available:

```php
public function haveSufficientQuantity(int $qty): bool
{
    return true; // Custom logic based on subscription slots
}
```

### Inventory and Stock Control

#### `isStockable(): bool`

Determines if the product uses inventory tracking:

```php
public function isStockable(): bool
{
    return false; // Subscriptions don't use traditional inventory
}
```

#### `totalQuantity(): int`

Returns total available quantity:

```php
public function totalQuantity(): int
{
    return $this->product->subscription_slots ?? 0;
}
```

### User Interface Control

#### `showQuantityBox(): bool`

Controls whether quantity input appears:

```php
public function showQuantityBox(): bool
{
    return true;
}
```

### Pricing Methods

#### `getProductPrices(): array`

Returns structured pricing data:

```php
public function getProductPrices(): array
{
    $basePrice = $this->product->price;
    $discount = $this->product->subscription_discount ?? 0;
    $finalPrice = $basePrice - ($basePrice * $discount / 100);
    
    return [
        'regular' => [
            'price' => core()->convertPrice($basePrice),
            'formatted_price' => core()->currency($basePrice),
        ],
        'final' => [
            'price' => core()->convertPrice($finalPrice),
            'formatted_price' => core()->currency($finalPrice),
        ],
    ];
}
```

#### `getPriceHtml(): string`

Generates price HTML for display:

```php
public function getPriceHtml(): string
{
    return view('subscription::products.prices.subscription', [
        'product' => $this->product,
        'prices' => $this->getProductPrices(),
    ])->render();
}
```

### Validation Methods

#### `getTypeValidationRules(): array`

Returns validation rules for product type specific fields:

```php
public function getTypeValidationRules(): array
{
    return [
        'subscription_frequency' => 'required|in:weekly,monthly,quarterly,yearly',
        'subscription_discount' => 'nullable|numeric|min:0|max:100',
        'subscription_duration' => 'nullable|integer|min:1',
        'subscription_slots' => 'required|integer|min:1',
    ];
}
```

### Admin Interface Customization

#### `$additionalViews` Property

Specifies additional blade views in product edit page:

```php
protected $additionalViews = [
    'subscription::admin.catalog.products.edit.subscription-settings',
    'subscription::admin.catalog.products.edit.subscription-pricing',
];
```

#### `$skipAttributes` Property

Specifies which attributes to skip:

```php
protected $skipAttributes = [
    'weight',
    'dimensions',
];
```

### Cart Integration

#### `prepareForCart(array $data): array`

Processes product data before adding to cart:

```php
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
```

---
