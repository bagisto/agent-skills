## Key Methods to Implement

| Method | Purpose | Required |
|--------|---------|----------|
| `calculate()` | Calculate and return shipping rate | Yes (abstract) |
| `getRate()` | Build CartShippingRate object | No (can be inline) |
| `isAvailable()` | Override for custom availability | No (uses default) |

## Built-in Shipping Methods

- **FlatRate**: `packages/Webkul/Shipping/src/Carriers/FlatRate.php`
- **Free**: `packages/Webkul/Shipping/src/Carriers/Free.php`

## Pricing Examples

### Fixed Rate Shipping

```php
public function calculate()
{
    if (! $this->isAvailable()) {
        return false;
    }

    $cartShippingRate = new CartShippingRate;
    $cartShippingRate->carrier = $this->getCode();
    $cartShippingRate->carrier_title = $this->getConfigData('title');
    $cartShippingRate->method = $this->getMethod();
    $cartShippingRate->method_title = $this->getConfigData('title');
    $cartShippingRate->method_description = $this->getConfigData('description');
    $cartShippingRate->price = 15.99;
    $cartShippingRate->base_price = 15.99;

    return $cartShippingRate;
}
```

### Weight-Based Pricing

```php
public function calculate()
{
    if (! $this->isAvailable()) {
        return false;
    }

    $cart = Cart::getCart();
    $baseRate = 5.00;
    $perKg = 2.50;

    $price = $baseRate + ($cart->weight * $perKg);

    $cartShippingRate = new CartShippingRate;
    $cartShippingRate->carrier = $this->getCode();
    $cartShippingRate->carrier_title = $this->getConfigData('title');
    $cartShippingRate->method = $this->getMethod();
    $cartShippingRate->method_title = $this->getConfigData('title');
    $cartShippingRate->price = core()->convertPrice($price);
    $cartShippingRate->base_price = $price;

    return $cartShippingRate;
}
```

### Free Shipping Above Threshold

```php
public function calculate()
{
    if (! $this->isAvailable()) {
        return false;
    }

    $cart = Cart::getCart();
    $threshold = (float) $this->getConfigData('free_shipping_threshold');
    $price = $cart->sub_total >= $threshold ? 0 : (float) $this->getConfigData('default_rate');

    $cartShippingRate = new CartShippingRate;
    $cartShippingRate->carrier = $this->getCode();
    $cartShippingRate->carrier_title = $this->getConfigData('title');
    $cartShippingRate->method = $this->getMethod();
    $cartShippingRate->method_title = $this->getConfigData('title');
    $cartShippingRate->price = core()->convertPrice($price);
    $cartShippingRate->base_price = $price;

    return $cartShippingRate;
}
```

## Shipping Facade

**Location:** `packages/Webkul/Shipping/src/Shipping.php`

The Shipping facade manages rate collection and processing:

```php
class Shipping
{
    public function collectRates()
    {
        // Iterates through all carriers and calls calculate()
        // Returns grouped shipping methods with rates
    }

    public function getGroupedAllShippingRates()
    {
        // Returns rates grouped by carrier
    }

    public function getShippingMethods()
    {
        // Returns available shipping methods
    }
}
```

## Package Structure

```
packages
└── Webkul
    └── CustomExpressShipping
        └── src
            ├── Carriers
            │   └── CustomExpressShipping.php         # Rate calculation logic
            ├── Config
            │   ├── carriers.php                     # Shipping method definition
            │   └── system.php                        # Admin configuration
            └── Providers
                └── CustomExpressShippingServiceProvider.php  # Registration
```

## Testing

Shipping methods can be tested through the checkout flow. Test:
- Method appears in checkout when enabled
- Rate calculation is correct
- Admin configuration saves properly
- Method respects enabled/disabled status

## Key Files Reference

| File | Purpose |
|------|---------|
| `packages/Webkul/Shipping/src/Carriers/AbstractShipping.php` | Base abstract class |
| `packages/Webkul/Shipping/src/Carriers/FlatRate.php` | Flat rate shipping example |
| `packages/Webkul/Shipping/src/Carriers/Free.php` | Free shipping example |
| `packages/Webkul/Shipping/src/Config/carriers.php` | Default carriers config |
| `packages/Webkul/Shipping/src/Shipping.php` | Shipping facade |
| `packages/Webkul/Checkout/src/Models/CartShippingRate.php` | Shipping rate model |
| `packages/Webkul/Admin/src/Config/system.php` | Admin config (carrier sections) |

## Common Pitfalls

- Forgetting to merge config in service provider
- Not matching `$code` property with config array key
- Not registering service provider in `bootstrap/providers.php`
- Forgetting to run `composer dump-autoload` after adding package
- Not clearing cache after configuration changes
- Not using `core()->convertPrice()` for multi-currency support
- Not checking `isStockable()` for per-item calculations
- Not following PHPDoc conventions with proper punctuation
